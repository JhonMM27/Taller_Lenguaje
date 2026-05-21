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
        from decimal import Decimal
        from django.conf import settings

        comprobante = Comprobante.objects.get(id=validated_data['comprobante_id'])
        serie_comprobante = comprobante.serie

        serie = 'FC01'
        if serie_comprobante:
            serie = serie_comprobante.serie
            if serie_comprobante.tipo == '01':
                serie = 'FC' + serie_comprobante.serie[2:] if len(serie_comprobante.serie) >= 2 else 'FC01'
            elif serie_comprobante.tipo == '03':
                serie = 'FB' + serie_comprobante.serie[2:] if len(serie_comprobante.serie) >= 2 else 'FB01'

        notas_existentes = NotaCredito.objects.filter(serie=serie).count()
        numero = notas_existentes + 1

        tasa_igv = Decimal(str(settings.IGV_TASA))
        op_gravada = Decimal('0.00')
        igv_total = Decimal('0.00')
        importe_total = Decimal('0.00')

        nota = NotaCredito.objects.create(
            comprobante_referencia=comprobante,
            serie=serie,
            numero=numero,
            tipo_nc=validated_data['tipo_nc'],
            tipo_nota=validated_data['tipo_nota'],
            estado='BORRADOR'
        )

        for det_data in validated_data['detalles']:
            producto_id = det_data['producto_id']
            cantidad = Decimal(str(det_data['cantidad']))
            precio_unitario = Decimal(str(det_data['precio_unitario']))
            descuento = Decimal(str(det_data.get('descuento', 0)))
            afecto_igv = det_data.get('afecto_igv', True)
            cod_tipo_afectacion = det_data.get('cod_tipo_afectacion', '10')

            producto = None
            if producto_id:
                from apps.productos.models import Producto
                try:
                    producto = Producto.objects.get(id=producto_id)
                except Producto.DoesNotExist:
                    pass

            bruto = cantidad * precio_unitario
            base = bruto - descuento
            if afecto_igv:
                igv_linea = round(base * tasa_igv, 2)
            else:
                igv_linea = Decimal('0.00')
            subtotal_linea = base + igv_linea

            DetalleNotaCredito.objects.create(
                nota_credito=nota,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                descuento=descuento,
                afecto_igv=afecto_igv,
                cod_tipo_afectacion=cod_tipo_afectacion,
                igv_linea=igv_linea,
                subtotal=subtotal_linea
            )

            op_gravada += base
            igv_total += igv_linea
            importe_total += subtotal_linea

        nota.op_gravada = op_gravada
        nota.igv = igv_total
        nota.importe = importe_total
        nota.save(update_fields=['op_gravada', 'igv', 'importe'])

        return nota
