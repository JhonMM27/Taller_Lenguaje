import base64
import hashlib
import logging
from datetime import date
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import pkcs12
from django.conf import settings

logger = logging.getLogger(__name__)

CERT_SALT = b'cert-encrypt'


def _get_derived_key() -> bytes:
    key = hashlib.pbkdf2_hmac(
        'sha256',
        settings.SECRET_KEY.encode(),
        CERT_SALT,
        100_000
    )
    return key


def get_fernet() -> Fernet:
    derived_key = _get_derived_key()
    fernet_key = base64.urlsafe_b64encode(derived_key)
    return Fernet(fernet_key)


def encrypt_password(password: str) -> bytes:
    fernet = get_fernet()
    return fernet.encrypt(password.encode())


def decrypt_password(encrypted: bytes) -> str:
    fernet = get_fernet()
    return fernet.decrypt(encrypted).decode()


def extraer_metadatos_pfx(pfx_bytes: bytes, password: str) -> dict:
    data = pkcs12.load_key_and_certificates(
        pfx_bytes, password.encode(), default_backend()
    )
    private_key, cert, ca_certs = data

    if cert is None:
        raise ValueError("El archivo PFX no contiene un certificado valido.")

    return {
        'numero_serie': str(cert.serial_number),
        'fecha_desde': cert.not_valid_before.date(),
        'fecha_hasta': cert.not_valid_after.date(),
        'huella': cert.fingerprint(hashes.SHA256()).hex(),
    }


def validar_pfx(pfx_bytes: bytes, password: str) -> bool:
    try:
        data = pkcs12.load_key_and_certificates(
            pfx_bytes, password.encode(), default_backend()
        )
        return data[1] is not None
    except Exception:
        return False


def get_cert_activo(empresa_ruc: str) -> Optional['Certificado']:
    from apps.empresas.models import Empresa, Certificado
    try:
        empresa = Empresa.objects.get(ruc=empresa_ruc)
        return Certificado.objects.filter(empresa=empresa, is_active=True).first()
    except Empresa.DoesNotExist:
        return None
