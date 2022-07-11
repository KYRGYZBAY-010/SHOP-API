from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from .serializers import MassageSerializers
from notifiers import get_notifier
from .token import bot_token, my_id


class MassageView(GenericAPIView):
    serializer_class = MassageSerializers

    def post(self, request):
        serializer = MassageSerializers(request.data)
        name = serializer.data['name']
        phone = serializer.data['phon']
        company = serializer.data['name_company']
        email = serializer.data['email']
        order = "ЗАЯВКА!: ""\n" + "Имя: " + str(name) + "\n" + "Телефон: " + str(phone) + "\n" + "Компания: " + str(company) + "\n" + "E-mail: " + str(email)
        telegram = get_notifier('telegram')
        telegram.notify(token= bot_token, chat_id=my_id, message=order)
        return Response('OK')

        