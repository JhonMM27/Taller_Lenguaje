from rest_framework import serializers as drf_serializers
from apps.clientes.models import Cliente


class ClienteSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

    def to_internal_value(self, data):
        """Normaliza campos del form."""
        if hasattr(data, 'dict'):
            normalized = data.dict()
        else:
            normalized = dict(data)

        # Si el form no envia 'activo', asumimos True (cliente nuevo por defecto).
        # Si envia 'activo', respetar el valor (on/true/1 -> True).
        if 'activo' in normalized:
            val = normalized['activo']
            if isinstance(val, bool):
                pass
            elif val in ('on', 'true', '1', True):
                normalized['activo'] = True
            else:
                normalized['activo'] = False
        else:
            normalized['activo'] = True

        return super().to_internal_value(normalized)

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

    def create(self, validated_data):
        """Al crear, si no se especifica 'activo' lo deja como True (default)."""
        validated_data['activo'] = validated_data.get('activo', True)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Al actualizar, respeta el valor enviado (permite desactivar)."""
        return super().update(instance, validated_data)