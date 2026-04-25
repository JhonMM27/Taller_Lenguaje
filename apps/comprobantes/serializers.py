from rest_framework import serializers
from apps.empresas.models import Empresa
from apps.clientes.models import Cliente
from apps.productos.models import Producto
from apps.comprobantes.models import Comprobante, DetalleComprobante, SerieComprobante, LogEnvioSUNAT
from apps.notas_credito.models import NotaCredito


class DetalleComprobanteSerializer(serializers.ModelSerializer):
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    producto_descripcion = serializers.CharField(source='producto.descripcion', read_only=True)

    class Meta:
        model = DetalleComprobante
        fields = ['id', 'producto', 'producto_codigo', 'producto_descripcion',
                  'cantidad', 'precio_unitario', 'descuento', 'afecto_igv',
                  'cod_tipo_afectacion', 'igv_linea', 'subtotal']


class ComprobanteSerializer(serializers.ModelSerializer):
    detalles = DetalleComprobanteSerializer(many=True, read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.razon_social', read_only=True)
    empresa_ruc = serializers.CharField(source='empresa.ruc', read_only=True)

    class Meta:
        model = Comprobante
        fields = ['id', 'empresa', 'empresa_ruc', 'cliente', 'cliente_nombre',
                  'serie', 'numero', 'fecha', 'tipo', 'estado',
                  'subtotal', 'igv', 'total', 'xml_firmado', 'detalles',
                  'created_at', 'updated_at']


class ComprobanteCreateSerializer(serializers.Serializer):
    empresa_id = serializers.IntegerField()
    cliente_id = serializers.IntegerField()
    fecha = serializers.DateField()
    tipo = serializers.CharField(max_length=2)
    detalles = serializers.ListField(child=serializers.DictField())

    def validate_tipo(self, value):
        if value not in ['01', '03']:
            raise serializers.ValidationError("Tipo debe ser 01 (Factura) o 03 (Boleta)")
        return value

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError("Debe incluir al menos un detalle")
        for detalle in value:
            if 'producto_id' not in detalle or 'cantidad' not in detalle:
                raise serializers.ValidationError("Cada detalle debe tener producto_id y cantidad")
        return value

    def create(self, validated_data):
        from django.db import transaction
        from django.conf import settings

        detalles_data = validated_data.pop('detalles')
        empresa = Empresa.objects.get(id=validated_data['empresa_id'])
        cliente = Cliente.objects.get(id=validated_data['cliente_id'])
        tipo = validated_data['tipo']

        with transaction.atomic():
            serie_obj, created = SerieComprobante.objects.get_or_create(
                empresa=empresa,
                tipo=tipo,
                defaults={'serie': 'F001' if tipo == '01' else 'B001', 'correlativo_actual': 0, 'activa': True}
            )

            if not created:
                serie_obj.refresh_from_db()

            serie_obj.correlativo_actual += 1
            numero = serie_obj.correlativo_actual
            serie_obj.save(update_fields=['correlativo_actual'])

            comprobante = Comprobante.objects.create(
                empresa=empresa,
                cliente=cliente,
                serie=serie_obj,
                numero=numero,
                fecha=validated_data['fecha'],
                tipo=tipo,
                estado='BORRADOR'
            )

            subtotal_total = 0
            igv_total = 0

            for det in detalles_data:
                producto = Producto.objects.get(id=det['producto_id'])
                cantidad = det['cantidad']
                precio_unitario = det.get('precio_unitario', producto.precio_unitario)
                afecto_igv = producto.afecto_igv

                base = float(precio_unitario) * float(cantidad)
                if afecto_igv:
                    igv_linea = round(base * settings.IGV_TASA, 2)
                else:
                    igv_linea = 0

                DetalleComprobante.objects.create(
                    comprobante=comprobante,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    descuento=det.get('descuento', 0),
                    afecto_igv=afecto_igv,
                    cod_tipo_afectacion=producto.cod_tipo_afectacion,
                    igv_linea=igv_linea,
                    subtotal=base
                )

                subtotal_total += base
                igv_total += igv_linea

            comprobante.subtotal = subtotal_total
            comprobante.igv = igv_total
            comprobante.total = subtotal_total + igv_total
            comprobante.save(update_fields=['subtotal', 'igv', 'total'])

        return comprobante


class LogEnvioSUNATSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEnvioSUNAT
        fields = '__all__'


class NotaCreditoSerializer(serializers.ModelSerializer):
    comprobante_numero = serializers.CharField(source='comprobante_referencia.numero', read_only=True)

    class Meta:
        model = NotaCredito
        fields = '__all__'


class NotaCreditoCreateSerializer(serializers.Serializer):
    comprobante_id = serializers.IntegerField()
    serie = serializers.CharField(max_length=4)
    fecha = serializers.DateField()
    tipo_nota = serializers.CharField(max_length=2)
    monto_afectado = serializers.DecimalField(max_digits=14, decimal_places=2)
    descripcion = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        comprobante = Comprobante.objects.get(id=data['comprobante_id'])
        if data['monto_afectado'] > comprobante.total:
            raise serializers.ValidationError("El monto afectado no puede exceder el total del comprobante original")
        return data

    def create(self, validated_data):
        comprobante = Comprobante.objects.get(id=validated_data['comprobante_id'])
        return NotaCredito.objects.create(
            comprobante_referencia=comprobante,
            serie=validated_data['serie'],
            numero=validated_data['numero'] if 'numero' in validated_data else 1,
            fecha=validated_data['fecha'],
            tipo_nota=validated_data['tipo_nota'],
            monto_afectado=validated_data['monto_afectado'],
            descripcion=validated_data.get('descripcion', ''),
            estado='BORRADOR'
        )