from rest_framework import serializers


class MassageSerializers(serializers.Serializer):
    name = serializers.CharField(max_length=50)
    phon = serializers.CharField(max_length=30)
    name_company = serializers.CharField(max_length=120)
    email = serializers.EmailField(max_length=120)
    

    class Meta:
        field = ['name', 'phon', 'name_company', 'email']