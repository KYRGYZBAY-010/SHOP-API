from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from .models import Project
from .serializers import ProjectDeteilSerializers, ProjectSerializers


class ProjectView(GenericAPIView):
    serialize_class = ProjectSerializers


    def get(self ,request):
        project = Project.objects.all()
        serializer = ProjectSerializers(project, many=True)
        return Response(serializer.data)
  

class ProjectDeteilView(GenericAPIView):
    serializer_class = ProjectDeteilSerializers


    def get(self, request, **kwargs):
        aid = kwargs['id']
        project = Project.objects.get(id=aid)
        serializer = ProjectDeteilSerializers(project)

        return Response(serializer.data)

