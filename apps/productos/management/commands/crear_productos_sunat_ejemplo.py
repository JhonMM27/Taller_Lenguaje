from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.productos.models import CategoriaProducto, Producto
from dominio.tributos import AFECTACIONES_IGV


PRODUCTOS_EJEMPLO = (
    ("10", "Producto gravado oneroso"),
    ("11", "Retiro gravado por premio"),
    ("12", "Retiro gravado por donacion"),
    ("13", "Retiro gravado general"),
    ("14", "Retiro gravado por publicidad"),
    ("15", "Bonificacion gravada"),
    ("16", "Entrega gravada a trabajadores"),
    ("17", "Arroz pilado sujeto a IVAP"),
    ("20", "Producto exonerado oneroso"),
    ("21", "Transferencia gratuita exonerada"),
    ("30", "Producto inafecto oneroso"),
    ("31", "Bonificacion inafecta"),
    ("32", "Retiro inafecto"),
    ("33", "Muestra medica inafecta"),
    ("34", "Entrega por convenio colectivo"),
    ("35", "Premio inafecto"),
    ("36", "Publicidad inafecta"),
    ("37", "Transferencia gratuita inafecta"),
    ("40", "Bien destinado a exportacion"),
)


class Command(BaseCommand):
    help = "Crea o actualiza un producto de ejemplo por afectacion IGV SUNAT."

    def handle(self, *args, **options):
        categoria, _ = CategoriaProducto.objects.update_or_create(
            nombre="EJEMPLOS SUNAT - AFECTACION IGV",
            defaults={
                "descripcion": "Productos de prueba para el Catalogo SUNAT N. 07",
                "codigo_sunat": "CAT07",
                "activo": True,
            },
        )

        creados = 0
        actualizados = 0
        for codigo_afectacion, descripcion in PRODUCTOS_EJEMPLO:
            datos = AFECTACIONES_IGV[codigo_afectacion]
            _, creado = Producto.objects.update_or_create(
                codigo=f"SUNAT-{codigo_afectacion}",
                defaults={
                    "descripcion": descripcion,
                    "unidad_medida": "NIU",
                    "precio_unitario": Decimal("100.00"),
                    "cod_tipo_afectacion": codigo_afectacion,
                    "afecto_igv": bool(datos["tasa"] and not datos["gratuito"]),
                    "categoria": categoria,
                    "activo": True,
                },
            )
            creados += int(creado)
            actualizados += int(not creado)

        self.stdout.write(self.style.SUCCESS(
            f"Productos SUNAT listos: {creados} creados, {actualizados} actualizados."
        ))
