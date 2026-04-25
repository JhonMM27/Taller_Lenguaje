from rest_framework import serializers
from apps.notas_credito.models import NotaCredito
from apps.comprobantes.models import Comprobante


class NotaCreditoSerializer(serializers.ModelSerializer):
    comprobante_numero = serializers.CharField(source='comprobante_referencia.numero', read_only=True)
    comprobante_total = serializers.DecimalField(source='comprobante_referencia.total', max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = NotaCredito
        fields = '__all__'


class NotaCreditoCreateSerializer(serializers.Serializer):
    comprobante_id = serializers.IntegerField()
    serie = serializers.CharField(max_length=4)
    fecha = serializers.DateField()
    tipo_nota = serializers.CharField(max_length=2)
    monto_afectado = serializers.DecimalField(max_digits=14, decimal_places=2)
    descripcion = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_monto_afectado(self, value):
        comprobante_id = self.initial_data.get('comprobante_id')
        try:
            comprobante = Comprobante.objects.get(id=comprobante_id)
            if value > comprobante.total:
                raise serializers.ValidationError(
                    "El monto afectado no puede exceder el total del comprobante original"
                )
        except Comprobante.DoesNotExist:
            raise serializers.ValidationError("Comprobante no encontrado")
        return value

    def create(self, validated_data):
        comprobante = Comprobante.objects.get(id=validated_data['comprobante_id'])
        return NotaCredito.objects.create(
            comprobante_referencia=comprobante,
            serie=validated_data['serie'],
            numero=1,
            fecha=validated_data['fecha'],
            tipo_nota=validated_data['tipo_nota'],
            monto_afectado=validated_data['monto_afectado'],
            descripcion=validated_data.get('descripcion', ''),
            estado='EMITIDO'
        )