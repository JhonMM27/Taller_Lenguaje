from rest_framework import serializers as drf_serializers
from apps.clientes.models import Cliente


class ClienteSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'