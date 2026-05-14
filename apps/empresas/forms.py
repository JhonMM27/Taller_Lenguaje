from django import forms
from django.core.files.uploadedfile import UploadedFile
from .models import Empresa, Certificado
from .services.certificado_service import (
    encrypt_password,
    extraer_metadatos_pfx,
    validar_pfx
)


class EmpresaForm(forms.ModelForm):
    cert_pfx = forms.FileField(
        label='Certificado Digital (.pfx)',
        required=False,
        help_text='Archivo de certificado digital para firma de comprobantes',
        widget=forms.FileInput(attrs={'accept': '.pfx,.p12'})
    )
    cert_password = forms.CharField(
        label='Contraseña del Certificado',
        required=False,
        help_text='Contraseña del archivo PFX',
        widget=forms.PasswordInput(render_value=False)
    )

    class Meta:
        model = Empresa
        fields = ['ruc', 'razon_social', 'nombre_comercial', 'direccion', 'telefono', 'email', 'regimen_tributario']
        widgets = {
            'telefono': forms.TextInput(attrs={'placeholder': '9XXXXXXXX'}),
            'email': forms.EmailInput(attrs={'placeholder': 'email@ejemplo.com'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        cert_pfx = cleaned_data.get('cert_pfx')
        cert_password = cleaned_data.get('cert_password')

        if cert_pfx and cert_password:
            if isinstance(cert_pfx, UploadedFile):
                cert_pfx.seek(0)
                pfx_bytes = cert_pfx.read()
                cert_pfx.seek(0)
            else:
                pfx_bytes = cert_pfx

            if len(pfx_bytes) == 0:
                cleaned_data.pop('cert_pfx', None)
                cleaned_data.pop('cert_password', None)
                cleaned_data.pop('cert_pfx_bytes', None)
                cleaned_data.pop('cert_metadatos', None)
                return cleaned_data

            if not validar_pfx(pfx_bytes, cert_password):
                raise forms.ValidationError('El certificado o la contraseña son inválidos.')

            try:
                metadatos = extraer_metadatos_pfx(pfx_bytes, cert_password)
                cleaned_data['cert_metadatos'] = metadatos
                cleaned_data['cert_pfx_bytes'] = pfx_bytes
            except Exception as e:
                raise forms.ValidationError(f'No se pudo leer el certificado: {str(e)}')

        return cleaned_data

    def save(self, commit=True):
        empresa = super().save(commit=commit)

        cert_pfx_bytes = self.cleaned_data.get('cert_pfx_bytes')
        cert_password = self.cleaned_data.get('cert_password')

        if cert_pfx_bytes and cert_password and commit:
            metadatos = self.cleaned_data['cert_metadatos']

            Certificado.objects.filter(empresa=empresa, is_active=True).update(is_active=False)

            Certificado.objects.create(
                empresa=empresa,
                nombre=f'Certificado de {empresa.razon_social}',
                certificado_binario=cert_pfx_bytes,
                contrasena=encrypt_password(cert_password),
                numero_serie=metadatos['numero_serie'],
                fecha_desde=metadatos['fecha_desde'],
                fecha_hasta=metadatos['fecha_hasta'],
                huella_digital=metadatos['huella'],
                is_active=True
            )

        return empresa
