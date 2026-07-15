"""
Helpers para empaquetado ZIP de comprobantes electronicos.

Funciones puras reutilizables tanto por adaptadores como por el dominio.
"""
from __future__ import annotations

import zipfile
from io import BytesIO


def crear_zip(xml_firmado: bytes, nombre_sin_extension: str) -> bytes:
    """
    Empaqueta un XML firmado en un archivo ZIP in-memory.

    Args:
        xml_firmado: contenido del XML firmado (bytes o str).
        nombre_sin_extension: nombre del archivo XML sin la extension.

    Returns:
        bytes con el ZIP.
    """
    if isinstance(xml_firmado, str):
        xml_firmado = xml_firmado.encode("utf-8")

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{nombre_sin_extension}.xml", xml_firmado)
    return buffer.getvalue()


def zip_nombre_comprobante(comprobante) -> str:
    """Genera el nombre del archivo ZIP segun convencion SUNAT.

    Formato: RUC-TIPO-SERIE-NUMERO.zip
    Ejemplo: 20100000001-01-F001-00000001.zip
    """
    # Si el comprobante viene de Django ORM
    if hasattr(comprobante, "empresa") and hasattr(comprobante.empresa, "ruc"):
        ruc = comprobante.empresa.ruc
    else:
        ruc = str(getattr(comprobante, "empresa_id", ""))
    tipo = getattr(comprobante, "tipo", "")
    serie_str = ""
    if hasattr(comprobante, "serie") and comprobante.serie:
        serie_str = getattr(comprobante.serie, "serie", "") or ""
    numero = getattr(comprobante, "numero", 0) or 0
    return f"{ruc}-{tipo}-{serie_str}-{numero:08d}.zip"