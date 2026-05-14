from rest_framework import serializers
from .models import Certificado, Empresa
from .services.certificado_service import (
    encrypt_password,
    decrypt_password,
    extraer_metadatos_pfx,
    validar_pfx
)


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ['id', 'ruc', 'razon_social', 'nombre_comercial', 'direccion', 'telefono', 'email', 'regimen_tributario']


class CertificadoSerializer(serializers.ModelSerializer):
    empresa_ruc = serializers.CharField(source='empresa.ruc', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.razon_social', read_only=True)
    is_vencido = serializers.SerializerMethodField()

    class Meta:
        model = Certificado
        fields = [
            'id', 'empresa', 'empresa_ruc', 'empresa_nombre',
            'nombre', 'numero_serie', 'fecha_desde', 'fecha_hasta',
            'huella_digital', 'is_active', 'is_vencido',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_vencido(self, obj):
        from datetime import date
        return obj.fecha_hasta < date.today()


class CertificadoCreateSerializer(serializers.Serializer):
    empresa_ruc = serializers.CharField(max_length=11)
    nombre = serializers.CharField(max_length=100)
    certificado_binario = serializers.FileField()
    contrasena = serializers.CharField(max_length=100, write_only=True)

    def validate_certificado_binario(self, value):
        if hasattr(value, 'content_type'):
            if value.content_type not in ['application/x-pkcs12', 'application/octet-stream']:
                if not value.name.endswith(('.pfx', '.p12')):
                    raise serializers.ValidationError(
                        "El archivo debe ser un certificado PFX/P12 (.pfx o .p12)"
                    )
        return value

    def validate_contrasena(self, value):
        if not value or len(value) < 1:
            raise serializers.ValidationError("La contrasena no puede estar vacia")
        return value

    def validate(self, attrs):
        empresa_ruc = attrs.get('empresa_ruc')
        try:
            empresa = Empresa.objects.get(ruc=empresa_ruc)
        except Empresa.DoesNotExist:
            raise serializers.ValidationError({'empresa_ruc': f'No existe empresa con RUC {empresa_ruc}'})

        pfx_bytes = attrs['certificado_binario'].read()
        password = attrs['contrasena']

        if not validar_pfx(pfx_bytes, password):
            raise serializers.ValidationError({'contrasena': 'Certificado o contrasena invalidos'})

        try:
            metadatos = extraer_metadatos_pfx(pfx_bytes, password)
        except Exception as e:
            raise serializers.ValidationError({'certificado_binario': f'No se pudo leer el certificado: {str(e)}'})

        attrs['empresa'] = empresa
        attrs['pfx_bytes'] = pfx_bytes
        attrs['metadatos'] = metadatos
        return attrs

    def create(self, validated_data):
        empresa = validated_data['empresa']
        pfx_bytes = validated_data['pfx_bytes']
        password = validated_data['contrasena']
        metadatos = validated_data['metadatos']

        cert = Certificado.objects.create(
            empresa=empresa,
            nombre=validated_data['nombre'],
            certificado_binario=pfx_bytes,
            contrasena=encrypt_password(password),
            numero_serie=metadatos['numero_serie'],
            fecha_desde=metadatos['fecha_desde'],
            fecha_hasta=metadatos['fecha_hasta'],
            huella_digital=metadatos['huella'],
            is_active=True
        )
        return cert
