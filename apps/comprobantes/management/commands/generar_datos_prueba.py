from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import random

from apps.empresas.models import Empresa, Certificado
from apps.clientes.models import Cliente
from apps.productos.models import CategoriaProducto, Producto
from apps.comprobantes.models import SerieComprobante, Comprobante, DetalleComprobante, LogEnvioSUNAT
from apps.notas_credito.models import NotaCredito


class Command(BaseCommand):
    help = 'Genera datos de prueba para reportes y dashboard (10+ registros por tabla)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando generación de datos de prueba...'))

        random.seed(42)

        # ============================================================
        # 1. EMPRESA
        # ============================================================
        self.stdout.write('Creando Empresa...')
        empresa, _ = Empresa.objects.get_or_create(
            ruc='20601234567',
            defaults={
                'razon_social': 'FARMACIA DEL SUR S.A.C.',
                'nombre_comercial': 'FarmaSur',
                'direccion': 'Av. Arequipa 1250, Lima',
                'telefono': '987654321',
                'email': 'admin@farmasur.com.pe',
                'regimen_tributario': 'GENERAL',
            }
        )
        self.stdout.write(f'  Empresa: {empresa}')

        # ============================================================
        # 2. CLIENTES (10 registros)
        # ============================================================
        self.stdout.write('Creando 10 Clientes...')
        clientes_data = [
            ('6', '20512345678', 'DISTRIBUIDORA NORTE S.A.C.', 'Jr. Unión 456, Trujillo', '941000001', 'ventas@distnorte.com'),
            ('6', '20598765432', 'CLINICA SAN MIGUEL E.I.R.L.', 'Av. Brasil 2890, Lima', '942000002', 'admin@clinicaSM.com'),
            ('6', '20511223344', 'LABORATORIOS FENIX S.A.', 'Calle Los Olivos 789, San Isidro', '943000003', 'compras@labfenix.pe'),
            ('6', '20555666777', 'HOSPITAL PRIVADO DEL PACIFICO', 'Av. Javier Prado 1520, San Borja', '944000004', 'facturacion@hpp.com.pe'),
            ('6', '20588999000', 'MINERA ANDES SUR S.A.A.', 'Av. El Derby 0250, Santiago de Surco', '945000005', 'tesoreria@mineraandes.com'),
            ('1', '72345678', 'Carlos Mendoza Rivera', 'Av. La Marina 3456, San Miguel', '946000006', 'carlos.mendoza@email.com'),
            ('1', '87654321', 'Maria Lopez Torres', 'Jr. Huallaga 234, Jesus Maria', '947000007', 'maria.lopez@email.com'),
            ('1', '45678912', 'Jose Garcia Quispe', 'Av. Salaverry 1890, Magdalena', '948000008', 'jose.garcia@email.com'),
            ('1', '65432198', 'Ana Rodriguez Chavez', 'Calle Schell 567, Miraflores', '949000009', 'ana.rodriguez@email.com'),
            ('1', '91234567', 'Pedro Sanchez Flores', 'Av. Petit Thouars 4321, Lince', '950000010', 'pedro.sanchez@email.com'),
        ]

        clientes = []
        for tipo_doc, num_doc, razon_social, direccion, telefono, email in clientes_data:
            cliente, _ = Cliente.objects.get_or_create(
                tipo_doc=tipo_doc,
                num_doc=num_doc,
                defaults={
                    'razon_social': razon_social,
                    'direccion': direccion,
                    'telefono': telefono,
                    'email': email,
                }
            )
            clientes.append(cliente)
            self.stdout.write(f'  Cliente: {cliente}')

        # ============================================================
        # 3. CATEGORIAS DE PRODUCTO (5 registros)
        # ============================================================
        self.stdout.write('Creando 5 Categorías...')
        categorias_data = [
            ('FARMACOS', '20100101', 'Medicamentos y productos farmacéuticos'),
            ('EQUIPOS_MED', '20200201', 'Equipos y dispositivos médicos'),
            ('INSUMOS', '20300301', 'Insumos y materiales descartables'),
            ('CONSULTAS', '20400401', 'Servicios de consulta médica'),
            ('LABORATORIO', '20500501', 'Análisis y pruebas de laboratorio'),
        ]

        categorias = []
        for nombre, codigo_sunat, descripcion in categorias_data:
            cat, _ = CategoriaProducto.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'descripcion': descripcion,
                    'codigo_sunat': codigo_sunat,
                    'activa': True,
                }
            )
            categorias.append(cat)
            self.stdout.write(f'  Categoría: {cat}')

        # ============================================================
        # 4. PRODUCTOS (10 registros)
        # ============================================================
        self.stdout.write('Creando 10 Productos...')
        productos_data = [
            ('MED001', 'Paracetamol 500mg x 20 tabletas', 'NIU', 15.50, True, '10', 'GRAVADA', categorias[0]),
            ('MED002', 'Ibuprofeno 400mg x 10 cápsulas', 'NIU', 22.00, True, '10', 'GRAVADA', categorias[0]),
            ('MED003', 'Amoxicilina 500mg x 21 cápsulas', 'NIU', 35.00, True, '10', 'GRAVADA', categorias[0]),
            ('MED004', 'Omeprazol 20mg x 14 cápsulas', 'NIU', 28.50, True, '10', 'GRAVADA', categorias[0]),
            ('EQ001', 'Tensiómetro digital automático', 'NIU', 180.00, True, '10', 'GRAVADA', categorias[1]),
            ('EQ002', 'Termómetro infrarrojo sin contacto', 'NIU', 95.00, True, '10', 'GRAVADA', categorias[1]),
            ('INS001', 'Guantes de nitrilo caja x 100', 'BX', 45.00, True, '10', 'GRAVADA', categorias[2]),
            ('INS002', 'Mascarillas N95 caja x 20', 'BX', 65.00, True, '10', 'GRAVADA', categorias[2]),
            ('CON001', 'Consulta médica general', 'NIU', 80.00, False, '20', 'EXONERADA', categorias[3]),
            ('LAB001', 'Análisis de sangre completo', 'NIU', 120.00, False, '20', 'EXONERADA', categorias[4]),
        ]

        productos = []
        for codigo, descripcion, unidad, precio, afecto_igv, cod_afect, tipo_op, categoria in productos_data:
            prod, _ = Producto.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'descripcion': descripcion,
                    'unidad_medida': unidad,
                    'precio_unitario': Decimal(str(precio)),
                    'afecto_igv': afecto_igv,
                    'cod_tipo_afectacion': cod_afect,
                    'tipo_operacion': tipo_op,
                    'categoria': categoria,
                }
            )
            productos.append(prod)
            self.stdout.write(f'  Producto: {prod}')

        # ============================================================
        # 5. SERIES DE COMPROBANTE
        # ============================================================
        self.stdout.write('Creando Series de Comprobante...')
        series_data = [
            ('01', 'F001'),
            ('03', 'B001'),
            ('07', 'FC01'),
        ]

        series = []
        for tipo, serie in series_data:
            s, _ = SerieComprobante.objects.get_or_create(
                empresa=empresa,
                tipo=tipo,
                serie=serie,
                defaults={'correlativo_actual': 0, 'activa': True}
            )
            series.append(s)
            self.stdout.write(f'  Serie: {s}')

        serie_factura = series[0]
        serie_boleta = series[1]
        serie_nc = series[2]

        # ============================================================
        # 6. COMPROBANTES (30+ registros distribuidos en 6 meses)
        # ============================================================
        self.stdout.write('Creando 30+ Comprobantes...')

        facturas_data = [
            (1, '2025-07-05', 0, clientes[0], 150, Decimal('3500.00')),
            (2, '2025-07-18', 0, clientes[1], 80, Decimal('2800.00')),
            (3, '2025-08-02', 0, clientes[2], 200, Decimal('4200.00')),
            (4, '2025-08-15', 0, clientes[3], 120, Decimal('3100.00')),
            (5, '2025-08-28', 0, clientes[4], 90, Decimal('2500.00')),
            (6, '2025-09-03', 0, clientes[0], 180, Decimal('4800.00')),
            (7, '2025-09-12', 0, clientes[1], 110, Decimal('3300.00')),
            (8, '2025-09-20', 0, clientes[2], 160, Decimal('4100.00')),
            (9, '2025-09-28', 0, clientes[3], 95, Decimal('2900.00')),
            (10, '2025-10-05', 0, clientes[4], 130, Decimal('3800.00')),
            (11, '2025-10-15', 0, clientes[0], 170, Decimal('4500.00')),
            (12, '2025-10-22', 0, clientes[1], 100, Decimal('3200.00')),
            (13, '2025-10-30', 0, clientes[2], 140, Decimal('3900.00')),
            (14, '2025-11-08', 0, clientes[3], 190, Decimal('5100.00')),
            (15, '2025-11-18', 0, clientes[4], 115, Decimal('3400.00')),
            (16, '2025-11-25', 0, clientes[0], 165, Decimal('4300.00')),
            (17, '2025-12-02', 0, clientes[1], 145, Decimal('3700.00')),
            (18, '2025-12-10', 0, clientes[2], 175, Decimal('4600.00')),
            (19, '2025-12-18', 0, clientes[3], 105, Decimal('2950.00')),
            (20, '2025-12-28', 0, clientes[4], 155, Decimal('4050.00')),
        ]

        boletas_data = [
            (1, '2025-07-10', 0, clientes[5], 50, Decimal('950.00')),
            (2, '2025-07-22', 0, clientes[6], 40, Decimal('720.00')),
            (3, '2025-08-08', 0, clientes[7], 60, Decimal('1100.00')),
            (4, '2025-08-20', 0, clientes[8], 35, Decimal('650.00')),
            (5, '2025-09-05', 0, clientes[9], 55, Decimal('1050.00')),
            (6, '2025-09-15', 0, clientes[5], 45, Decimal('850.00')),
            (7, '2025-10-08', 0, clientes[6], 65, Decimal('1200.00')),
            (8, '2025-10-20', 0, clientes[7], 30, Decimal('580.00')),
            (9, '2025-11-05', 0, clientes[8], 70, Decimal('1350.00')),
            (10, '2025-11-15', 0, clientes[9], 42, Decimal('780.00')),
            (11, '2025-12-05', 0, clientes[5], 58, Decimal('1080.00')),
            (12, '2025-12-15', 0, clientes[6], 38, Decimal('690.00')),
        ]

        comprobantes = []
        correlativo_factura = 0
        correlativo_boleta = 0

        for num, fecha_str, estado_idx, cliente, cantidad, total in facturas_data:
            fecha = date.fromisoformat(fecha_str)
            subtotal = round(total / Decimal('1.18'), 2)
            igv = total - subtotal
            correlativo_factura += 1

            comp = Comprobante.objects.create(
                empresa=empresa,
                cliente=cliente,
                serie=serie_factura,
                numero=correlativo_factura,
                fecha=fecha,
                tipo='01',
                estado='ACEPTADO',
                subtotal=subtotal,
                igv=igv,
                total=total,
            )
            comprobantes.append(comp)

            DetalleComprobante.objects.create(
                comprobante=comp,
                producto=productos[num % len(productos)],
                cantidad=Decimal(str(cantidad)),
                precio_unitario=productos[num % len(productos)].precio_unitario,
                afecto_igv=True,
                subtotal=subtotal,
                igv_linea=igv,
            )

            self.stdout.write(f'  Factura: {comp.serie.serie}-{comp.numero:08d} | {fecha} | S/ {total}')

        for num, fecha_str, estado_idx, cliente, cantidad, total in boletas_data:
            fecha = date.fromisoformat(fecha_str)
            subtotal = round(total / Decimal('1.18'), 2)
            igv = total - subtotal
            correlativo_boleta += 1

            comp = Comprobante.objects.create(
                empresa=empresa,
                cliente=cliente,
                serie=serie_boleta,
                numero=correlativo_boleta,
                fecha=fecha,
                tipo='03',
                estado='ACEPTADO',
                subtotal=subtotal,
                igv=igv,
                total=total,
            )
            comprobantes.append(comp)

            DetalleComprobante.objects.create(
                comprobante=comp,
                producto=productos[num % len(productos)],
                cantidad=Decimal(str(cantidad)),
                precio_unitario=productos[num % len(productos)].precio_unitario,
                afecto_igv=True,
                subtotal=subtotal,
                igv_linea=igv,
            )

            self.stdout.write(f'  Boleta: {comp.serie.serie}-{comp.numero:08d} | {fecha} | S/ {total}')

        # ============================================================
        # 7. NOTAS DE CRÉDITO (3 registros)
        # ============================================================
        self.stdout.write('Creando 3 Notas de Crédito...')
        notas_data = [
            (comprobantes[5], 'FC01', 1, '2025-09-15', '01', Decimal('1200.00'), 'Anulación por devolución de mercadería'),
            (comprobantes[10], 'FC01', 2, '2025-10-18', '03', Decimal('850.00'), 'Corrección por error en descripción'),
            (comprobantes[17], 'FC01', 3, '2025-12-12', '07', Decimal('690.00'), 'Devolución total'),
        ]

        for comp_ref, serie, numero, fecha_str, tipo_nota, monto, desc in notas_data:
            nc = NotaCredito.objects.create(
                comprobante_referencia=comp_ref,
                serie=serie,
                numero=numero,
                fecha=date.fromisoformat(fecha_str),
                tipo_nota=tipo_nota,
                monto_afectado=monto,
                descripcion=desc,
                estado='EMITIDO',
            )
            self.stdout.write(f'  Nota Crédito: {nc}')

        # ============================================================
        # 8. LOGS DE ENVÍO SUNAT (10 registros)
        # ============================================================
        self.stdout.write('Creando 10 Logs de Envío SUNAT...')
        logs_data = [
            (comprobantes[0], '0', 'ACEPTADO', 'Comprobante aceptado correctamente'),
            (comprobantes[1], '0', 'ACEPTADO', 'Comprobante aceptado correctamente'),
            (comprobantes[2], '0', 'ACEPTADO', 'Comprobante aceptado correctamente'),
            (comprobantes[3], '0', 'ACEPTADO', 'Comprobante aceptado correctamente'),
            (comprobantes[4], '0', 'ACEPTADO', 'Comprobante aceptado correctamente'),
            (comprobantes[5], '0', 'ACEPTADO', 'Comprobante aceptado correctamente'),
            (comprobantes[6], '0', 'ACEPTADO', 'Comprobante aceptado correctamente'),
            (comprobantes[7], '0', 'ACEPTADO', 'Comprobante aceptado correctamente'),
            (comprobantes[8], '0', 'ACEPTADO', 'Comprobante aceptado correctamente'),
            (comprobantes[9], '0', 'ACEPTADO', 'Comprobante aceptado correctamente'),
        ]

        for comp, cod, estado, desc in logs_data:
            log = LogEnvioSUNAT.objects.create(
                comprobante=comp,
                estado_respuesta=estado,
                codigo_respuesta=cod,
                descripcion=desc,
                uuid=f'UUID-{random.randint(100000, 999999)}',
            )
            self.stdout.write(f'  Log: {log}')

        # ============================================================
        # RESUMEN
        # ============================================================
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('RESUMEN DE DATOS GENERADOS'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'  Empresas:          {Empresa.objects.count()}')
        self.stdout.write(f'  Clientes:          {Cliente.objects.count()}')
        self.stdout.write(f'  Categorías:        {CategoriaProducto.objects.count()}')
        self.stdout.write(f'  Productos:         {Producto.objects.count()}')
        self.stdout.write(f'  Series:            {SerieComprobante.objects.count()}')
        self.stdout.write(f'  Comprobantes:      {Comprobante.objects.count()}')
        self.stdout.write(f'  Detalles:          {DetalleComprobante.objects.count()}')
        self.stdout.write(f'  Notas de Crédito:  {NotaCredito.objects.count()}')
        self.stdout.write(f'  Logs SUNAT:        {LogEnvioSUNAT.objects.count()}')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Datos de prueba generados exitosamente!'))
