from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from .models import Project, Clients, Comment
from .serializers import ProjectDeteilSerializers, ProjectSerializers, ClientsSerializers, CommentSerializers, LaikSerializers


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

class CommentView(GenericAPIView):
    serializer_class = CommentSerializers


    def post(self, request):
        serializer = CommentSerializers(data=request.data, many=False)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.data)

class LaiksView(GenericAPIView):
    serializer_class = LaikSerializers


    def post(self, request):
        serializer = LaikSerializers(data=request.data, many=False)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.data)