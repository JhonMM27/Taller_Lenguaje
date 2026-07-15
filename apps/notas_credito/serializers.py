from rest_framework import serializers
from apps.notas_credito.models import NotaCredito, DetalleNotaCredito
from apps.comprobantes.models import Comprobante, DetalleComprobante


class DetalleComprobanteSerializer(serializers.ModelSerializer):
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    producto_descripcion = serializers.CharField(source='producto.descripcion', read_only=True)

    class Meta:
        model = DetalleComprobante
        fields = ['id', 'producto', 'producto_codigo', 'producto_descripcion', 'cantidad', 'precio_unitario', 'descuento', 'afecto_igv', 'cod_tipo_afectacion', 'igv_linea', 'subtotal']


class DetalleNotaCreditoSerializer(serializers.ModelSerializer):
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    producto_descripcion = serializers.CharField(source='producto.descripcion', read_only=True)

    class Meta:
        model = DetalleNotaCredito
        fields = ['id', 'producto', 'producto_codigo', 'producto_descripcion', 'cantidad', 'precio_unitario', 'descuento', 'afecto_igv', 'cod_tipo_afectacion', 'igv_linea', 'subtotal']


class NotaCreditoSerializer(serializers.ModelSerializer):
    comprobante_numero = serializers.CharField(source='comprobante_referencia.numero', read_only=True)
    comprobante_serie = serializers.CharField(source='comprobante_referencia.serie.serie', read_only=True)
    comprobante_cliente = serializers.CharField(source='comprobante_referencia.cliente.razon_social', read_only=True)
    comprobante_codigo = serializers.CharField(source='comprobante_referencia.cliente.codigo', read_only=True)
    tipo_nota_display = serializers.CharField(source='get_tipo_nota_display', read_only=True)
    detalles = DetalleNotaCreditoSerializer(many=True, read_only=True)

    class Meta:
        model = NotaCredito
        fields = '__all__'


class NotaCreditoCreateSerializer(serializers.Serializer):
    comprobante_id = serializers.IntegerField()
    tipo_nc = serializers.CharField(max_length=3)
    tipo_nota = serializers.CharField(max_length=2)
    detalles = serializers.ListField(child=serializers.DictField())

    def validate_comprobante_id(self, value):
        try:
            Comprobante.objects.get(id=value)
        except Comprobante.DoesNotExist:
            raise serializers.ValidationError("Comprobante no encontrado")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        usuario = request.user if request else None
        
        # Calculate/set monto_afectado for validation if needed, or pass validated_data
        # We can calculate the total affected amount from details if not specified.
        if 'monto_afectado' not in validated_data:
            from decimal import Decimal
            monto_afectado = Decimal('0.00')
            for det in validated_data.get('detalles', []):
                monto_afectado += Decimal(str(det['cantidad'])) * Decimal(str(det['precio_unitario']))
            validated_data['monto_afectado'] = monto_afectado

        from apps.notas_credito.services import NotaCreditoService
        return NotaCreditoService.emitir(validated_data, usuario=usuario)
