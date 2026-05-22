from rest_framework import serializers as drf_serializers
from apps.clientes.models import Cliente


class ClienteSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

    def validate(self, attrs):
        instance = self.instance or Cliente()
        for field, value in attrs.items():
            setattr(instance, field, value)
            
        from django.core.exceptions import ValidationError
        try:
            instance.clean()
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                raise drf_serializers.ValidationError(e.message_dict)
            else:
                raise drf_serializers.ValidationError(e.messages)
        return attrs