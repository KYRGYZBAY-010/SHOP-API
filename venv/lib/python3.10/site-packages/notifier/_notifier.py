# -*- coding: utf-8 -*-

#    Copyright (C) 2014 Yahoo! Inc. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import collections
import contextlib
import copy
import inspect
import logging
import threading
import weakref

try:
    weak_method = weakref.WeakMethod
except AttributeError:
    import weakrefmethod
    weak_method = weakrefmethod.WeakMethod

from frozendict import frozendict
import futurist
from oslo_utils import reflection
from oslo_utils import uuidutils
import six

from notifier import _constants

LOG = logging.getLogger(__name__)

_Notified = collections.namedtuple("_Notified", 'total,successes,failures')


def _make_ref(callback, weak=False):
    if not weak:
        return callback
    if inspect.ismethod(callback):
        return weak_method(callback)
    else:
        return weakref.ref(callback)


class Listener(object):
    """Immutable helper that represents a notification listener/target."""

    def __init__(self, callback,
                 args=None, kwargs=None, details_filter=None,
                 weak=False):
        """Initialize members

        :param callback: callback function
        :param details_filter: a callback that will be called before the
                               actual callback that can be used to discard
                               the event (thus avoiding the invocation of
                               the actual callback)
        :param args: non-keyworded arguments
        :type args: list/iterable/tuple
        :param kwargs: key-value pair arguments
        :type kwargs: dictionary
        :param weak: whether the callback provided is referenced via a
                     weak reference or a strong reference
        :type weak: bool
        """
        self._uuid = uuidutils.generate_uuid()
        self._callback = callback
        self._details_filter = details_filter
        self._weak = weak
        if not args:
            self._args = ()
        else:
            if not isinstance(args, tuple):
                self._args = tuple(args)
            else:
                self._args = args
        if not kwargs:
            self._kwargs = frozendict()
        else:
            self._kwargs = frozendict(kwargs)

    @property
    def callback(self):
        """Callback (may be none) to call with event + details.

        If the callback is maintained via a weak reference, and that
        weak reference has been collected, this will be none instead of
        an actual callback.
        """
        if self._weak:
            return self._callback()
        return self._callback

    @property
    def details_filter(self):
        """Callback (may be none) to call to discard events + details."""
        return self._details_filter

    @property
    def uuid(self):
        """Unique identifier that uniquely identifies this listener."""
        return self._uuid

    @property
    def dead(self):
        """Whether the callback no longer exists.

        If the callback is maintained via a weak reference, and that
        weak reference has been collected, this will be true
        instead of false.
        """
        if not self._weak:
            return False
        cb = self._callback()
        if cb is None:
            return True
        return False

    @property
    def kwargs(self):
        """Frozen dictionary of keyword arguments to use in future calls."""
        return self._kwargs

    @property
    def args(self):
        """Tuple of positional arguments to use in future calls."""
        return self._args

    def __call__(self, event_type, details):
        """Activate the target callback with the given event + details.

        NOTE(harlowja): if a details filter callback exists and it returns
        a falsey value when called with the provided ``details``, then the
        target callback will **not** be called.
        """
        cb = self.callback
        if cb is None:
            return
        if self._details_filter is not None:
            if not self._details_filter(details):
                return
        kwargs = dict(self._kwargs)
        kwargs['details'] = details
        cb(event_type, *self._args, **kwargs)

    def __repr__(self):
        cb = self.callback
        if cb is None:
            repr_msg = "%s object at 0x%x; dead" % (
                reflection.get_class_name(self, fully_qualified=False),
                id(self))
        else:
            repr_msg = "%s object at 0x%x calling into '%r'" % (
                reflection.get_class_name(self, fully_qualified=False),
                id(self), cb)
            if self._details_filter is not None:
                repr_msg += " using details filter '%r'" % self._details_filter
        return "<%s>" % repr_msg

    def is_equivalent(self, callback, details_filter=None):
        """Check if the callback provided is the same as the internal one.

        :param callback: callback used for comparison
        :param details_filter: callback used for comparison
        :returns: false if not the same callback, otherwise true
        :rtype: boolean
        """
        cb = self.callback
        if cb is None and callback is not None:
            return False
        if cb is not None and callback is None:
            return False
        if cb is not None and callback is not None \
           and not reflection.is_same_callback(cb, callback):
            return False
        if details_filter is not None:
            if self._details_filter is None:
                return False
            else:
                return reflection.is_same_callback(self._details_filter,
                                                   details_filter)
        else:
            return self._details_filter is None

    def __eq__(self, other):
        """Checks if the provided listener is equivalent.

        Does **not** check that the provided listener has the same uuid or
        arguments or keyword arguments (only checks that the provided
        listener has the same callback and details filter callback).
        """
        if isinstance(other, Listener):
            return self.is_equivalent(other.callback,
                                      details_filter=other._details_filter)
        else:
            return NotImplemented


class Notifier(object):
    """A notification (`pub/sub`_ *like*) helper class.

    It is intended to be used to subscribe to notifications of events
    occurring as well as allow a entity to post said notifications to any
    associated subscribers without having either entity care about how this
    notification occurs.

    .. _pub/sub: http://en.wikipedia.org/wiki/Publish%E2%80%93subscribe_pattern
    """

    #: Keys that can *not* be used in callbacks arguments
    RESERVED_KEYS = ('details',)

    #: Kleene star constant that is used to recieve all notifications
    ANY = _constants.ANY

    #: Events which can *not* be used to trigger notifications
    DISALLOWED_NOTIFICATION_EVENTS = frozenset([ANY])

    LOG = None
    """
    Logger that can be used to log failures (if none the module logger is
    used instead).
    """

    def __init__(self):
        self._topics = {}
        self._lock = threading.Lock()
        self._logger = self.LOG or LOG
        self._executor = futurist.SynchronousExecutor()

    def __getstate__(self):
        return {
            'topics': self._topics,
        }

    def __setstate__(self, dct):
        self._topics = dct['topics']
        self._lock = threading.Lock()
        self._logger = self.LOG or LOG
        self._executor = futurist.SynchronousExecutor()

    def __len__(self):
        """Returns how many callbacks are registered.

        :returns: count of how many callbacks are registered
        :rtype: number
        """
        count = 0
        topics = set(six.iterkeys(self._topics))
        while topics:
            event_type = topics.pop()
            try:
                listeners = self._topics[event_type]
                count += len(listeners)
            except KeyError:
                pass
        return count

    def is_registered(self, event_type, callback, details_filter=None):
        """Check if a callback is registered.

        :param event_type: event type callback was registered to
        :param callback: callback that was used during registration
        :param details_filter: details filter that was used during
                               registration

        :returns: if the callback is registered
        :rtype: boolean
        """
        listeners = self._topics.get(event_type, [])
        for listener in listeners:
            if listener.is_equivalent(callback, details_filter=details_filter):
                return True
        return False

    def reset(self):
        """Forget all previously registered callbacks."""
        self._topics.clear()

    def _do_dispatch(self, listeners, event_type, details):
        """Calls into listeners, handling failures and logging as needed."""
        possible_calls = len(listeners)
        call_failures = 0
        for listener in listeners:
            try:
                listener(event_type, details.copy())
            except Exception:
                self._logger.warn(
                    "Failure calling listener %s to notify about event"
                    " %s, details: %s", listener, event_type, details,
                    exc_info=True)
                call_failures += 1
        return _Notified(possible_calls,
                         possible_calls - call_failures,
                         call_failures)

    def notify(self, event_type, details):
        """Notify about an event occurrence.

        All callbacks registered to receive notifications about given
        event type will be called. If the provided event type can not be
        used to emit notifications (this is checked via
        the :meth:`.can_be_registered` method) then a value error will be
        raised.

        :param event_type: event type that occurred
        :param details: additional event details *dictionary* passed to
                        callback keyword argument with the same name
        :type details: dictionary

        :returns: a future object that will have a result named tuple with
                  contents being (total listeners called, how many listeners
                  were **successfully** called, how many listeners
                  were not **successfully** called); do note that the result
                  may be delayed depending on internal executor used.
        """
        if not self.can_trigger_notification(event_type):
            raise ValueError("Event type '%s' is not allowed to trigger"
                             " notifications" % event_type)
        listeners = list(self._topics.get(self.ANY, []))
        listeners.extend(self._topics.get(event_type, []))
        if not details:
            details = {}
        fut = self._executor.submit(self._do_dispatch, listeners,
                                    event_type, details)
        return fut

    def register(self, event_type, callback,
                 args=None, kwargs=None, details_filter=None,
                 weak=False):
        """Register a callback to be called when event of a given type occurs.

        Callback will be called with provided ``args`` and ``kwargs`` and
        when event type occurs (or on any event if ``event_type`` equals to
        :attr:`.ANY`). It will also get additional keyword argument,
        ``details``, that will hold event details provided to the
        :meth:`.notify` method (if a details filter callback is provided then
        the target callback will *only* be triggered if the details filter
        callback returns a truthy value).

        :param event_type: event type to get triggered on
        :param callback: function callback to be registered.
        :param args: non-keyworded arguments
        :type args: list
        :param kwargs: key-value pair arguments
        :type kwargs: dictionary
        :param weak: if the callback retained should be referenced via
                     a weak reference or a strong reference (defaults to
                     holding a strong reference)
        :type weak: bool

        :returns: the listener that was registered
        :rtype: :py:class:`~.Listener`
        """
        if not six.callable(callback):
            raise ValueError("Event callback must be callable")
        if details_filter is not None:
            if not six.callable(details_filter):
                raise ValueError("Details filter must be callable")
        if not self.can_be_registered(event_type):
            raise ValueError("Disallowed event type '%s' can not have a"
                             " callback registered" % event_type)
        if kwargs:
            for k in self.RESERVED_KEYS:
                if k in kwargs:
                    raise KeyError("Reserved key '%s' not allowed in "
                                   "kwargs" % k)
        with self._lock:
            if self.is_registered(event_type, callback,
                                  details_filter=details_filter):
                raise ValueError("Event callback already registered with"
                                 " equivalent details filter")
            listener = Listener(_make_ref(callback, weak=weak),
                                args=args, kwargs=kwargs,
                                details_filter=details_filter,
                                weak=weak)
            listeners = self._topics.setdefault(event_type, [])
            listeners.append(listener)
            return listener

    def deregister(self, event_type, callback, details_filter=None):
        """Remove a single listener bound to event ``event_type``.

        :param event_type: deregister listener bound to event_type
        :param callback: callback that was used during registration
        :param details_filter: details filter that was used during
                               registration

        :returns: if a listener was deregistered
        :rtype: boolean
        """
        with self._lock:
            listeners = self._topics.get(event_type, [])
            for i, listener in enumerate(listeners):
                if listener.is_equivalent(callback,
                                          details_filter=details_filter):
                    listeners.pop(i)
                    return True
            return False

    def deregister_by_uuid(self, event_type, uuid):
        """Remove a single listener bound to event ``event_type``.

        :param event_type: deregister listener bound to event_type
        :param uuid: uuid of listener to remove

        :returns: if the listener was deregistered
        :rtype: boolean
        """
        with self._lock:
            listeners = self._topics.get(event_type, [])
            for i, listener in enumerate(listeners):
                if listener.uuid == uuid:
                    listeners.pop(i)
                    return True
            return False

    def deregister_event(self, event_type):
        """Remove a group of listeners bound to event ``event_type``.

        :param event_type: deregister listeners bound to event_type

        :returns: how many callbacks were deregistered
        :rtype: int
        """
        return len(self._topics.pop(event_type, []))

    def copy(self):
        """Clones this notifier (and its bound listeners)."""
        c = copy.copy(self)
        c._topics = {}
        c._lock = threading.Lock()
        topics = set(six.iterkeys(self._topics))
        while topics:
            event_type = topics.pop()
            try:
                listeners = self._topics[event_type]
                c._topics[event_type] = list(listeners)
            except KeyError:
                pass
        return c

    def listeners_iter(self):
        """Return an iterator over the mapping of event => listeners bound.

        The listener list(s) returned should **not** be mutated.

        NOTE(harlowja): Each listener in the yielded (event, listeners)
        tuple is an instance of the :py:class:`~.Listener`  type, which
        itself wraps a provided callback (and its details filter
        callback, if any).
        """
        topics = set(six.iterkeys(self._topics))
        while topics:
            event_type = topics.pop()
            try:
                yield event_type, self._topics[event_type]
            except KeyError:
                pass

    def can_be_registered(self, event_type):
        """Checks if the event can be registered/subscribed to.

        :returns: whether the event_type can be registered/subscribed to.
        :rtype: boolean
        """
        return True

    def can_trigger_notification(self, event_type):
        """Checks if the event can trigger a notification.

        :param event_type: event that needs to be verified
        :returns: whether the event can trigger a notification
        :rtype: boolean
        """
        if event_type in self.DISALLOWED_NOTIFICATION_EVENTS:
            return False
        else:
            return True


class RestrictedNotifier(Notifier):
    """A notification class that restricts events registered/triggered.

    NOTE(harlowja): This class unlike :class:`.Notifier` restricts and
    disallows registering callbacks for event types that are not declared
    when constructing the notifier.
    """

    def __init__(self, watchable_events, allow_any=True):
        super(RestrictedNotifier, self).__init__()
        self._watchable_events = frozenset(watchable_events)
        self._allow_any = allow_any

    def __getstate__(self):
        dct = super(RestrictedNotifier, self).__getstate__()
        dct['watchables'] = self._watchable_events
        dct['allow_any'] = self._allow_any
        return dct

    def __setstate__(self, dct):
        super(RestrictedNotifier, self).__setstate__(dct)
        self._watchable_events = dct['watchables']
        self._allow_any = dct['allow_any']

    def events_iter(self):
        """Returns iterator of events that can be registered/subscribed to.

        NOTE(harlowja): does not include back the ``ANY`` event type as that
        meta-type is not a specific event but is a capture-all that does not
        imply the same meaning as specific event types.
        """
        for event_type in self._watchable_events:
            yield event_type

    def can_be_registered(self, event_type):
        """Checks if the event can be registered/subscribed to.

        :param event_type: event that needs to be verified
        :returns: whether the event can be registered/subscribed to
        :rtype: boolean
        """
        return (event_type in self._watchable_events or
                (event_type == self.ANY and self._allow_any))


@contextlib.contextmanager
def register_deregister(notifier, event_type, callback=None,
                        args=None, kwargs=None, details_filter=None,
                        weak=False):
    """Context manager that registers a callback, then deregisters on exit.

    NOTE(harlowja): if the callback is none, then this registers nothing, which
                    is different from the behavior of the ``register`` method
                    which will *not* accept none as it is not callable...
    """
    if callback is None:
        yield
    else:
        notifier.register(event_type, callback,
                          args=args, kwargs=kwargs,
                          details_filter=details_filter,
                          weak=weak)
        try:
            yield
        finally:
            notifier.deregister(event_type, callback,
                                details_filter=details_filter)
