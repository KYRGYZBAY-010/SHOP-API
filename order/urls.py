from django.urls import path
from .views import MassageView


urlpatterns = [
    path('', MassageView.as_view(), name='bot'),
]