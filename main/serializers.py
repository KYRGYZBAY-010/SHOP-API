from rest_framework import serializers
from .models import Project


class ProjectSerializers(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ('img', 'title', 'txt', 'date')


class ProjectDeteilSerializers(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'img', 'title', 'txt', 'date')