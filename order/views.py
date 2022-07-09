from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from .bot import massage
from .serializers import MassageSerializers


class MassageView(GenericAPIView):
    serializer_class = MassageSerializers

    def post(self, request):
        serializer = MassageSerializers(request.data)
        name = serializer.data['name']
        phone = serializer.data['phon']
        company = serializer.data['name_company']
        email = serializer.data['email']
        order = "*Заявка с сайта*: " + "*Имя*: " + str(name) + "\n" + "*Телефон*: " + str(phone) + "\n" + "*Компания*: " + str(company) + "\n" + "*E-mail*: " + str(email)
        massage(order)
        return Response('OK')
