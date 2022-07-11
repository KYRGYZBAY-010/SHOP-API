from unittest.util import _MAX_LENGTH
from rest_framework import serializers
from .models import Project, Clients, Search


class ProjectSerializers(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ('img', 'title')


class ProjectDeteilSerializers(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'title', 'img', 'img_1', 'img_2', 'img_3', 'txt', 'date', 'site', 'insta', 'title2')


class ClientsSerializers(serializers.ModelSerializer):
    class Meta:
        model = Clients
        fields = ('title', 'icon', 'url')
