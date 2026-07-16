"""Catalogos SUNAT de afectacion del IGV y tributos asociados."""
from decimal import Decimal


TRIBUTOS_SUNAT = {
    "1000": {"descripcion": "Impuesto General a las Ventas", "nombre": "IGV", "tipo": "VAT"},
    "1016": {"descripcion": "Impuesto a la Venta de Arroz Pilado", "nombre": "IVAP", "tipo": "VAT"},
    "2000": {"descripcion": "Impuesto Selectivo al Consumo", "nombre": "ISC", "tipo": "EXC"},
    "3000": {"descripcion": "Impuesto a la Renta", "nombre": "IR", "tipo": "TOX"},
    "7152": {"descripcion": "Impuesto al Consumo de Bolsas de Plastico", "nombre": "ICBPER", "tipo": "OTH"},
    "9995": {"descripcion": "Exportacion", "nombre": "EXP", "tipo": "FRE"},
    "9996": {"descripcion": "Gratuito", "nombre": "GRA", "tipo": "FRE"},
    "9997": {"descripcion": "Exonerado", "nombre": "EXO", "tipo": "VAT"},
    "9998": {"descripcion": "Inafecto", "nombre": "INA", "tipo": "FRE"},
    "9999": {"descripcion": "Otros tributos", "nombre": "OTROS", "tipo": "OTH"},
}


AFECTACIONES_IGV = {
    "10": {"descripcion": "Gravado - Operacion onerosa", "categoria": "S", "tributo_id": "1000", "nombre": "IGV", "tipo": "VAT", "tasa": Decimal("18.00"), "gratuito": False},
    "11": {"descripcion": "Gravado - Retiro por premio", "categoria": "Z", "tributo_id": "9996", "nombre": "GRA", "tipo": "FRE", "tasa": Decimal("18.00"), "gratuito": True},
    "12": {"descripcion": "Gravado - Retiro por donacion", "categoria": "Z", "tributo_id": "9996", "nombre": "GRA", "tipo": "FRE", "tasa": Decimal("18.00"), "gratuito": True},
    "13": {"descripcion": "Gravado - Retiro", "categoria": "Z", "tributo_id": "9996", "nombre": "GRA", "tipo": "FRE", "tasa": Decimal("18.00"), "gratuito": True},
    "14": {"descripcion": "Gravado - Retiro por publicidad", "categoria": "Z", "tributo_id": "9996", "nombre": "GRA", "tipo": "FRE", "tasa": Decimal("18.00"), "gratuito": True},
    "15": {"descripcion": "Gravado - Bonificaciones", "categoria": "Z", "tributo_id": "9996", "nombre": "GRA", "tipo": "FRE", "tasa": Decimal("18.00"), "gratuito": True},
    "16": {"descripcion": "Gravado - Retiro por entrega a trabajadores", "categoria": "Z", "tributo_id": "9996", "nombre": "GRA", "tipo": "FRE", "tasa": Decimal("18.00"), "gratuito": True},
    "17": {"descripcion": "Gravado - IVAP", "categoria": "S", "tributo_id": "1016", "nombre": "IVAP", "tipo": "VAT", "tasa": Decimal("4.00"), "gratuito": False},
    "20": {"descripcion": "Exonerado - Operacion onerosa", "categoria": "E", "tributo_id": "9997", "nombre": "EXO", "tipo": "VAT", "tasa": Decimal("0.00"), "gratuito": False},
    "21": {"descripcion": "Exonerado - Transferencia gratuita", "categoria": "Z", "tributo_id": "9996", "nombre": "GRA", "tipo": "FRE", "tasa": Decimal("0.00"), "gratuito": True},
    "30": {"descripcion": "Inafecto - Operacion onerosa", "categoria": "O", "tributo_id": "9998", "nombre": "INA", "tipo": "FRE", "tasa": Decimal("0.00"), "gratuito": False},
    "31": {"descripcion": "Inafecto - Retiro por bonificacion", "categoria": "Z", "tributo_id": "9996", "nombre": "GRA", "tipo": "FRE", "tasa": Decimal("0.00"), "gratuito": True},
    "32": {"descripcion": "Inafecto - Retiro", "categoria": "Z", "tributo_id": "9996", "nombre": "GRA", "tipo": "FRE", "tasa": Decimal("0.00"), "gratuito": True},
    "33": {"descripcion": "Inafecto - Retiro por muestras medicas", "categoria": "Z", "tributo_id": "9996", "nombre": "GRA", "tipo": "FRE", "tasa": Decimal("0.00"), "gratuito": True},
    "34": {"descripcion": "Inafecto - Retiro por convenio colectivo", "categoria": "Z", "tributo_id": "9996", "nombre": "GRA", "tipo": "FRE", "tasa": Decimal("0.00"), "gratuito": True},
    "35": {"descripcion": "Inafecto - Retiro por premio", "categoria": "Z", "tributo_id": "9996", "nombre": "GRA", "tipo": "FRE", "tasa": Decimal("0.00"), "gratuito": True},
    "36": {"descripcion": "Inafecto - Retiro por publicidad", "categoria": "Z", "tributo_id": "9996", "nombre": "GRA", "tipo": "FRE", "tasa": Decimal("0.00"), "gratuito": True},
    "37": {"descripcion": "Inafecto - Transferencia gratuita", "categoria": "Z", "tributo_id": "9996", "nombre": "GRA", "tipo": "FRE", "tasa": Decimal("0.00"), "gratuito": True},
    "40": {"descripcion": "Exportacion de bienes o servicios", "categoria": "G", "tributo_id": "9995", "nombre": "EXP", "tipo": "FRE", "tasa": Decimal("0.00"), "gratuito": False},
}

AFECTACION_IGV_CHOICES = tuple(
    (codigo, f"{codigo} - {datos['descripcion']}")
    for codigo, datos in AFECTACIONES_IGV.items()
)
CODIGOS_GRATUITOS = frozenset(
    codigo for codigo, datos in AFECTACIONES_IGV.items() if datos["gratuito"]
)

TIPO_OPERACION_VENTA_INTERNA = "0101"
TIPO_OPERACION_EXPORTACION_BIENES = "0200"
TIPOS_OPERACION_SOPORTADOS = (
    TIPO_OPERACION_VENTA_INTERNA,
    TIPO_OPERACION_EXPORTACION_BIENES,
)
MONEDAS_SUNAT = (
    ("PEN", "Sol peruano (PEN)"),
    ("USD", "Dolar estadounidense (USD)"),
    ("EUR", "Euro (EUR)"),
)
CODIGOS_MONEDA_SUNAT = frozenset(codigo for codigo, _ in MONEDAS_SUNAT)


def datos_afectacion_igv(codigo: str) -> dict:
    codigo = str(codigo or "").strip()
    if codigo not in AFECTACIONES_IGV:
        raise ValueError(f"Codigo de afectacion del IGV no permitido por SUNAT: {codigo}")
    return dict(AFECTACIONES_IGV[codigo])


def tipo_operacion_para(codigo: str) -> str:
    datos = datos_afectacion_igv(codigo)
    if datos["gratuito"]:
        return "GRATUITA"
    return {"20": "EXONERADA", "30": "INAFECTA", "40": "EXPORTACION"}.get(
        str(codigo), "GRAVADA"
    )


def tipo_operacion_comprobante(codigos_afectacion) -> str:
    """Deriva el Catalogo 51 y evita mezclar exportacion con venta interna."""
    codigos = [str(codigo or "").strip() for codigo in codigos_afectacion]
    if not codigos:
        raise ValueError("El comprobante debe incluir al menos una linea")
    for codigo in codigos:
        datos_afectacion_igv(codigo)
    contiene_exportacion = "40" in codigos
    if contiene_exportacion and any(codigo != "40" for codigo in codigos):
        raise ValueError(
            "Una exportacion de bienes no puede mezclar productos con afectacion 40 "
            "y operaciones nacionales en el mismo comprobante."
        )
    if contiene_exportacion:
        return TIPO_OPERACION_EXPORTACION_BIENES
    return TIPO_OPERACION_VENTA_INTERNA


def validar_moneda(codigo: str) -> str:
    codigo = str(codigo or "PEN").strip().upper()
    if codigo not in CODIGOS_MONEDA_SUNAT:
        raise ValueError(f"Moneda no soportada para SUNAT: {codigo}")
    return codigo
