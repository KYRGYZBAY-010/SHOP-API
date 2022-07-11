from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from .models import Project, Clients
from .serializers import ProjectDeteilSerializers, ProjectSerializers, ClientsSerializers


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

class ClientsView(GenericAPIView):
    serlializer_class = ClientsSerializers

    def get(self, request):
        client = Clients.objects.all()
        serializer = ClientsSerializers(client, many = True)
        return Response(serializer.data)


class Search(GenericAPIView):
    serializer_class = ProjectSerializers


    def get(self, request, name):
        search = Project.objects.filter(title__icontains = name)
        serializer = ProjectSerializers(search, many = True)
        return Response(serializer.data)
