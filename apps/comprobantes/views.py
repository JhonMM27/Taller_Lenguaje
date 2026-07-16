"""
Views web del módulo de Comprobantes.

Views delgadas: solo reciben request, llaman al service y devuelven response.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import transaction
from django.contrib import messages
from datetime import datetime
import csv
import io

from apps.comprobantes.models import (
    Comprobante, SerieComprobante, ImportacionComprobante, DetalleComprobante
)
from apps.comprobantes.services import ComprobanteService
from apps.empresas.models import Empresa
from apps.clientes.models import Cliente
from apps.productos.models import Producto, CategoriaProducto
from apps.core.exceptions import (
    AppError, EstadoInvalido, ComprobanteNoEncontrado,
    TipoDocumentoInvalido, EmpresaNoEncontrada, ClienteNoEncontrado,
    ReglaNegocioViolada,
)


@login_required
def lista_comprobantes(request):
    tipo = request.GET.get('tipo', '')
    estado = request.GET.get('estado', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    cliente_id = request.GET.get('cliente_id', '')

    comprobantes = Comprobante.objects.select_related('cliente', 'empresa', 'serie').all()

    if tipo:
        comprobantes = comprobantes.filter(tipo=tipo)
    if estado:
        comprobantes = comprobantes.filter(estado=estado)
    if fecha_desde:
        comprobantes = comprobantes.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        comprobantes = comprobantes.filter(fecha__lte=fecha_hasta)
    if cliente_id:
        comprobantes = comprobantes.filter(cliente_id=cliente_id)

    from django.core.paginator import Paginator

    comprobantes = comprobantes.order_by('-fecha', '-creado_en')
    paginator = Paginator(comprobantes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'comprobantes': page_obj,
        'tipos': SerieComprobante.TIPO_CHOICES,
        'estados': Comprobante.ESTADO_CHOICES,
        'empresas': Empresa.objects.all(),
        'clientes': Cliente.objects.all(),
        'productos': Producto.objects.all(),
        'today': datetime.now().strftime('%Y-%m-%d'),
        'cliente_name_selected': Cliente.objects.get(id=cliente_id).razon_social if cliente_id else ''
    }
    return render(request, 'comprobantes/lista.html', context)


@login_required
def crear_comprobante(request):
    """View delgada: delega al ComprobanteService.crear()."""
    if request.method == 'POST':
        detalles_data = _detalles_desde_post(request)

        if not detalles_data:
            return render(request, 'comprobantes/crear.html', {
                'errors': {'detalles': ['Debe seleccionar al menos un producto']},
                **_contexto_creacion(request),
            })

        try:
            comprobante = ComprobanteService.crear(
                data={
                    'empresa_id': int(request.POST.get('empresa_id')),
                    'cliente_id': int(request.POST.get('cliente_id')),
                    'fecha': request.POST.get('fecha'),
                    'tipo': request.POST.get('tipo'),
                    'moneda': request.POST.get('moneda', 'PEN'),
                    'detalles': detalles_data,
                },
                usuario=request.user,
            )
            messages.success(request, f'Comprobante {comprobante} creado exitosamente')
            return redirect('comprobantes:lista')
        except TipoDocumentoInvalido as e:
            messages.error(request, str(e))
        except (EmpresaNoEncontrada, ClienteNoEncontrado) as e:
            messages.error(request, str(e))
        except AppError as e:
            messages.error(request, str(e))

    return render(request, 'comprobantes/crear.html', _contexto_creacion(request))


def _contexto_creacion(request):
    empresas = Empresa.objects.filter(activo=True)
    datos = request.POST if request.method == 'POST' else {}
    detalles_form = _detalles_desde_post(request) if request.method == 'POST' else []
    return {
        'empresas': empresas,
        'clientes': Cliente.objects.filter(activo=True),
        'productos': Producto.objects.filter(activo=True),
        'today': datetime.now().strftime('%Y-%m-%d'),
        'empresa_default': empresas.first() if empresas.count() == 1 else None,
        'form_data': datos,
        'detalles_form': detalles_form or [{}],
    }


def _detalles_desde_post(request):
    producto_ids = request.POST.getlist('producto_id')
    cantidades = request.POST.getlist('cantidad')
    precios = request.POST.getlist('precio_unitario')
    descuentos = request.POST.getlist('descuento')
    afectaciones = request.POST.getlist('cod_tipo_afectacion')
    detalles = []
    for i, producto_id in enumerate(producto_ids):
        if not str(producto_id).strip():
            continue
        detalles.append({
            'producto_id': producto_id,
            'cantidad': cantidades[i] if i < len(cantidades) else '1',
            'precio_unitario': precios[i] if i < len(precios) else '0',
            'descuento': descuentos[i] if i < len(descuentos) else '0',
            'cod_tipo_afectacion': afectaciones[i] if i < len(afectaciones) else None,
        })
    return detalles


def _contexto_formulario(comprobante, modo):
    return {
        'comprobante': comprobante,
        'modo': modo,
        'clientes': Cliente.objects.filter(activo=True),
        'productos': Producto.objects.filter(activo=True),
        'detalles_iniciales': comprobante.detalles.select_related('producto').all(),
        'tipo_inicial': comprobante.tipo,
        'monedas': Comprobante.MONEDA_CHOICES,
    }


@login_required
def editar_comprobante(request, pk):
    comprobante = get_object_or_404(Comprobante, pk=pk, activo=True)
    if comprobante.estado != 'BORRADOR':
        messages.error(request, 'Solo se pueden editar comprobantes en BORRADOR.')
        return redirect('comprobantes:detalle', pk=pk)
    if request.method == 'POST':
        try:
            actualizado = ComprobanteService.actualizar_borrador(
                pk,
                {
                    'cliente_id': int(request.POST.get('cliente_id')),
                    'fecha': request.POST.get('fecha'),
                    'moneda': request.POST.get('moneda', comprobante.moneda),
                    'detalles': _detalles_desde_post(request),
                },
                usuario=request.user,
            )
            messages.success(request, f'Borrador {actualizado} actualizado correctamente.')
            return redirect('comprobantes:detalle', pk=actualizado.pk)
        except (ValueError, TypeError, AppError) as exc:
            messages.error(request, str(exc))
    return render(
        request, 'comprobantes/form_edicion.html',
        _contexto_formulario(comprobante, 'editar'),
    )


@login_required
def corregir_comprobante(request, pk):
    comprobante = get_object_or_404(Comprobante, pk=pk, activo=True)
    if comprobante.estado != 'RECHAZADO':
        messages.error(request, 'Solo se corrigen de esta forma comprobantes RECHAZADOS.')
        return redirect('comprobantes:detalle', pk=pk)
    if comprobante.tiene_reemplazo:
        messages.info(request, 'Este rechazo ya tiene un comprobante de reemplazo.')
        return redirect('comprobantes:detalle', pk=comprobante.reemplazado_por.pk)
    if request.method == 'POST':
        try:
            nuevo = ComprobanteService.corregir_rechazado(
                pk,
                {
                    'cliente_id': int(request.POST.get('cliente_id')),
                    'fecha': request.POST.get('fecha'),
                    'moneda': request.POST.get('moneda', comprobante.moneda),
                    'detalles': _detalles_desde_post(request),
                },
                usuario=request.user,
            )
            messages.success(
                request,
                f'Se genero {nuevo.get_tipo_display()} {nuevo} con nueva numeracion.',
            )
            return redirect('comprobantes:detalle', pk=nuevo.pk)
        except (ValueError, TypeError, AppError) as exc:
            messages.error(request, str(exc))
    return render(
        request, 'comprobantes/form_edicion.html',
        _contexto_formulario(comprobante, 'corregir'),
    )


@login_required
def detalle_comprobante(request, pk):
    comprobante = get_object_or_404(
        Comprobante.objects.select_related('cliente', 'empresa', 'serie'), pk=pk
    )
    return render(request, 'comprobantes/detalle.html', {'comprobante': comprobante})


@login_required
def ver_pdf(request, pk):
    comprobante = get_object_or_404(Comprobante, pk=pk)
    from django.template.loader import render_to_string
    from weasyprint import HTML

    html_string = render_to_string('comprobantes/pdf_template.html', {
        'comprobante': comprobante,
        'detalles': comprobante.detalles.all(),
    })

    html = HTML(string=html_string)
    pdf_content = html.write_pdf()

    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{comprobante.nombre_xml}.pdf"'
    return response


@login_required
def descargar_xml(request, pk):
    comprobante = get_object_or_404(Comprobante, pk=pk)
    if not comprobante.xml_firmado:
        return HttpResponse("XML no disponible", status=404)

    import xml.dom.minidom
    try:
        dom = xml.dom.minidom.parseString(comprobante.xml_firmado)
        pretty_xml = dom.toprettyxml(indent="  ")
        pretty_xml = "\n".join([line for line in pretty_xml.splitlines() if line.strip()])
    except Exception:
        pretty_xml = comprobante.xml_firmado

    response = HttpResponse(pretty_xml.encode('utf-8'), content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="{comprobante.nombre_xml}"'
    return response


@login_required
def descargar_cdr(request, pk):
    """Permite al usuario descargar el CDR (ZIP) del comprobante desde la base de datos."""
    comprobante = get_object_or_404(Comprobante, pk=pk)
    
    log_cdr = comprobante.logs.filter(cdr_xml__isnull=False).exclude(cdr_xml='').first()
    
    if not log_cdr or not log_cdr.cdr_xml:
        return HttpResponse("El CDR no está disponible para este comprobante.", status=404)
        
    try:
        import base64
        cdr_bytes = base64.b64decode(log_cdr.cdr_xml)
        nombre_cdr_zip = f"R-{comprobante.nombre_zip}"
        
        response = HttpResponse(cdr_bytes, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{nombre_cdr_zip}"'
        return response
    except Exception as e:
        return HttpResponse(f"Error al procesar el archivo del CDR: {str(e)}", status=500)


@login_required
def descargar_excel_comprobante(request, pk):
    comprobante = get_object_or_404(
        Comprobante.objects.select_related('cliente', 'empresa', 'serie'), pk=pk
    )
    import pandas as pd
    from io import BytesIO

    output = BytesIO()
    
    detalles = []
    for d in comprobante.detalles.all():
        detalles.append({
            'CÓDIGO': d.producto.codigo,
            'DESCRIPCIÓN': d.producto.descripcion,
            'CANT.': float(d.cantidad),
            'P. UNIT': float(d.precio_unitario),
            'SUBTOTAL': float(d.subtotal),
            'IGV': float(d.igv_linea),
            'TOTAL': float(d.subtotal + d.igv_linea)
        })
    
    df_detalles = pd.DataFrame(detalles)
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_detalles.to_excel(writer, sheet_name='Comprobante', startrow=10, index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Comprobante']
        
        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#4F46E5', 'font_color': 'white',
            'border': 1, 'align': 'center'
        })
        title_fmt = workbook.add_format({'bold': True, 'font_size': 18, 'font_color': '#1E293B'})
        subtitle_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#4F46E5'})
        data_fmt = workbook.add_format({'font_size': 10})
        num_fmt = workbook.add_format({'num_format': 'S/ #,##0.00', 'font_size': 10})
        
        worksheet.write('A1', f'{comprobante.get_tipo_display().upper()} ELECTRÓNICA', title_fmt)
        worksheet.write('A2', f'{comprobante.serie.serie}-{comprobante.numero:08d}', subtitle_fmt)
        
        worksheet.write('A4', 'EMISOR:', data_fmt)
        worksheet.write('B4', comprobante.empresa.razon_social, data_fmt)
        worksheet.write('A5', 'RUC:', data_fmt)
        worksheet.write('B5', comprobante.empresa.ruc, data_fmt)
        
        worksheet.write('E4', 'CLIENTE:', data_fmt)
        worksheet.write('F4', comprobante.cliente.razon_social, data_fmt)
        worksheet.write('E5', 'DOC:', data_fmt)
        worksheet.write('F5', comprobante.cliente.num_doc, data_fmt)
        worksheet.write('E6', 'FECHA:', data_fmt)
        worksheet.write('F6', str(comprobante.fecha), data_fmt)

        for col_num, value in enumerate(df_detalles.columns.values):
            worksheet.write(10, col_num, value, header_fmt)
            
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 40)
        worksheet.set_column('C:G', 12)
        
        row_total = 10 + len(df_detalles) + 2
        worksheet.write(row_total, 5, 'SUBTOTAL:', data_fmt)
        worksheet.write(row_total, 6, float(comprobante.subtotal), num_fmt)
        worksheet.write(row_total + 1, 5, 'IGV (18%):', data_fmt)
        worksheet.write(row_total + 1, 6, float(comprobante.igv), num_fmt)
        worksheet.write(row_total + 2, 5, 'TOTAL:', subtitle_fmt)
        worksheet.write(row_total + 2, 6, float(comprobante.total), num_fmt)

    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = (
        f'attachment; filename="Comprobante_{comprobante.serie.serie}_{comprobante.numero}.xlsx"'
    )
    return response


@login_required
def reintentar_comprobante(request, pk):
    """Reintenta solo fallos tecnicos; nunca rechazos tributarios."""
    if request.method != 'POST':
        return redirect('comprobantes:detalle', pk=pk)
    try:
        comprobante = ComprobanteService.reintentar_envio(pk)
        messages.success(request, f'Envio de {comprobante} reintentado exitosamente')
    except EstadoInvalido as e:
        messages.error(request, str(e))
    except ComprobanteNoEncontrado as e:
        messages.error(request, str(e))
    except AppError as e:
        messages.error(request, str(e))
    return redirect('comprobantes:detalle', pk=pk)


@login_required
def emitir_comprobante(request, pk):
    """View delgada: delega al ComprobanteService.emitir()."""
    if request.method != 'POST':
        return redirect('comprobantes:detalle', pk=pk)
    try:
        comprobante = ComprobanteService.emitir(pk)
        messages.success(request, f'Comprobante {comprobante} emitido exitosamente')
    except EstadoInvalido as e:
        messages.error(request, str(e))
    except ComprobanteNoEncontrado as e:
        messages.error(request, str(e))
    except AppError as e:
        messages.error(request, str(e))
    return redirect('comprobantes:detalle', pk=pk)


# ==============================================================================
# SECCIÓN: IMPORTACIÓN DE COMPROBANTES DESDE ARCHIVOS CSV / EXCEL
# ==============================================================================

def clean_val(val, default=''):
    """Limpia valores de CSV/Excel: maneja None, NaN de pandas y fechas datetime."""
    if val is None:
        return default
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return default
    except Exception:
        pass
    if hasattr(val, 'strftime'):
        return val.strftime('%Y-%m-%d')
    return str(val).strip()


def parse_date(date_str):
    if not date_str:
        return datetime.now().date()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    from apps.core.exceptions import ReglaNegocioViolada
    raise ReglaNegocioViolada(f"Formato de fecha no válido: {date_str}")


COLUMNAS_IMPORTACION_REQUERIDAS = {
    'tipo', 'serie', 'numero', 'fecha', 'cliente_tipo_doc',
    'cliente_num_doc', 'cliente_nombre', 'producto_codigo',
    'producto_descripcion', 'cantidad', 'precio_unitario',
}
EXTENSIONES_IMPORTACION = ('.csv', '.xlsx')
TAMANO_MAX_IMPORTACION = 10 * 1024 * 1024


def _decimal_importacion(valor, campo, row_num, *, mayor_que_cero=False):
    from decimal import Decimal, InvalidOperation

    texto = clean_val(valor, '')
    try:
        numero = Decimal(texto)
    except (InvalidOperation, ValueError, TypeError):
        raise ReglaNegocioViolada(
            f"Fila {row_num}: '{campo}' debe ser un número válido."
        )
    if mayor_que_cero and numero <= 0:
        raise ReglaNegocioViolada(
            f"Fila {row_num}: '{campo}' debe ser mayor que cero."
        )
    if not mayor_que_cero and numero < 0:
        raise ReglaNegocioViolada(
            f"Fila {row_num}: '{campo}' no puede ser negativo."
        )
    return numero


def _validar_columnas_importacion(columnas):
    normalizadas = {
        clean_val(col).lower() for col in ([] if columnas is None else columnas)
        if col
    }
    faltantes = sorted(COLUMNAS_IMPORTACION_REQUERIDAS - normalizadas)
    if faltantes:
        raise ReglaNegocioViolada(
            "Faltan columnas obligatorias: " + ', '.join(faltantes)
        )


def _procesar_fila_comprobante(row, row_num, empresa):
    """Procesa una fila de forma atómica; un error no deja datos parciales."""
    from decimal import Decimal
    from dominio.entidades.comprobante import DetalleComprobante as DetalleDominio
    from dominio.tributos import (
        datos_afectacion_igv,
        tipo_operacion_comprobante,
        validar_moneda,
    )
    from apps.comprobantes.services import _validar_tipo_cliente

    tipo_raw = clean_val(row.get('tipo'), '01')
    TIPO_MAP = {
        '1': '01', '01': '01',
        '3': '03', '03': '03',
        '7': '07', '07': '07',
        '8': '08', '08': '08',
    }
    tipo = TIPO_MAP.get(tipo_raw.strip(), tipo_raw.strip().zfill(2))
    if tipo not in ('01', '03'):
        raise ReglaNegocioViolada(
            f"Fila {row_num}: tipo '{tipo}' no permitido; use 01 o 03."
        )
    serie = clean_val(row.get('serie'), '')

    numero_str = clean_val(row.get('numero'), '0')
    try:
        numero_decimal = Decimal(numero_str)
        if numero_decimal != numero_decimal.to_integral_value():
            raise ValueError
        numero = int(numero_decimal)
    except Exception:
        raise ReglaNegocioViolada(
            f"Fila {row_num}: 'numero' debe ser un entero positivo."
        )
    if numero <= 0:
        raise ReglaNegocioViolada(
            f"Fila {row_num}: 'numero' debe ser mayor que cero."
        )

    fecha_str = clean_val(row.get('fecha'), '')
    cliente_tipo_doc = clean_val(row.get('cliente_tipo_doc'), '6')
    cliente_num_doc = clean_val(row.get('cliente_num_doc'), '')
    cliente_nombre = clean_val(row.get('cliente_nombre'), 'Cliente Varios')
    producto_codigo = clean_val(row.get('producto_codigo'), '')

    cantidad = _decimal_importacion(
        row.get('cantidad'), 'cantidad', row_num, mayor_que_cero=True
    )
    precio_unitario = _decimal_importacion(
        row.get('precio_unitario'), 'precio_unitario', row_num
    )

    categoria_nombre = clean_val(row.get('categoria'), '')

    if not serie or not cliente_num_doc or not cliente_nombre or not producto_codigo:
        raise ReglaNegocioViolada(
            f"Fila {row_num}: serie, cliente_num_doc, cliente_nombre y "
            "producto_codigo son obligatorios."
        )

    serie_obj = SerieComprobante.objects.filter(
        empresa=empresa, serie=serie, tipo=tipo, activo=True
    ).first()

    if not serie_obj:
        raise ReglaNegocioViolada(
            f"Fila {row_num}: la serie '{serie}' del tipo '{tipo}' no existe "
            f"o no está activa para {empresa.razon_social}."
        )

    existe = Comprobante.objects.filter(serie=serie_obj, numero=numero).exists()
    if existe:
        raise ReglaNegocioViolada(
            f"Fila {row_num}: comprobante {serie}-{numero:08d} ya existe."
        )

    fecha = parse_date(fecha_str)
    moneda = validar_moneda(clean_val(row.get('moneda'), 'PEN'))
    pais_codigo = clean_val(row.get('pais_codigo'), 'PE').upper()
    afectacion_solicitada = clean_val(row.get('afectacion_igv'), '')

    with transaction.atomic():
        categoria = None
        if categoria_nombre:
            categoria, _ = CategoriaProducto.objects.get_or_create(
                nombre__iexact=categoria_nombre,
                defaults={'nombre': categoria_nombre}
            )

        producto_existente = Producto.objects.filter(codigo=producto_codigo).first()
        afectacion = afectacion_solicitada or (
            producto_existente.cod_tipo_afectacion if producto_existente else '10'
        )
        datos_tributo = datos_afectacion_igv(afectacion)

        producto, _ = Producto.objects.get_or_create(
            codigo=producto_codigo,
            defaults={
                'descripcion': clean_val(
                    row.get('producto_descripcion'), producto_codigo
                ),
                'precio_unitario': precio_unitario,
                'categoria': categoria,
                'cod_tipo_afectacion': afectacion,
            }
        )

        cliente, _ = Cliente.objects.get_or_create(
            tipo_doc=cliente_tipo_doc,
            num_doc=cliente_num_doc,
            defaults={
                'razon_social': cliente_nombre,
                'pais_codigo': pais_codigo,
            }
        )
        tipo_operacion = tipo_operacion_comprobante([afectacion])
        _validar_tipo_cliente(tipo, cliente, tipo_operacion)

        detalle_dominio = DetalleDominio(
            id=None,
            producto_id=producto.id,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            cod_tipo_afectacion=afectacion,
            afecto_igv=bool(datos_tributo['tasa'] and not datos_tributo['gratuito']),
        )
        detalle_dominio.calcular_subtotal(Decimal(str(settings.IGV_TASA)))

        comprobante = Comprobante.objects.create(
            empresa=empresa,
            cliente=cliente,
            serie=serie_obj,
            numero=numero,
            fecha=fecha,
            tipo=tipo,
            tipo_operacion=tipo_operacion,
            moneda=moneda,
            estado='BORRADOR',
            subtotal=detalle_dominio.subtotal,
            igv=detalle_dominio.igv_linea,
            total=detalle_dominio.total_linea,
        )

        DetalleComprobante.objects.create(
            comprobante=comprobante,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            afecto_igv=detalle_dominio.afecto_igv,
            cod_tipo_afectacion=afectacion,
            subtotal=detalle_dominio.subtotal,
            igv_linea=detalle_dominio.igv_linea,
        )
        if numero > serie_obj.correlativo_actual:
            serie_obj.correlativo_actual = numero
            serie_obj.save(update_fields=['correlativo_actual'])
    return 1


@login_required
def importar_csv(request):
    if request.method == 'POST':
        archivo = request.FILES.get('archivo_csv')
        if not archivo:
            messages.error(request, 'No se seleccionó ningún archivo')
            return redirect('comprobantes:importar')

        nombre_archivo = archivo.name
        nombre_normalizado = (nombre_archivo or '').lower()
        if not nombre_normalizado.endswith(EXTENSIONES_IMPORTACION):
            messages.error(request, 'Formato no permitido. Use solamente CSV o XLSX.')
            return redirect('comprobantes:importar')
        if archivo.size > TAMANO_MAX_IMPORTACION:
            messages.error(request, 'El archivo supera el tamaño máximo de 10 MB.')
            return redirect('comprobantes:importar')

        empresa_id = clean_val(request.POST.get('empresa_id'), '')
        empresa = (
            Empresa.objects.filter(pk=int(empresa_id), activo=True).first()
            if empresa_id.isdigit()
            else None
        )
        if not empresa:
            messages.error(request, 'Seleccione una empresa emisora válida.')
            return redirect('comprobantes:importar')

        try:
            importacion = ImportacionComprobante.objects.create(
                archivo_csv=archivo,
                usuario=request.user,
                estado='PROCESANDO'
            )
        except (PermissionError, OSError):
            importacion = ImportacionComprobante(
                usuario=request.user,
                estado='PROCESANDO'
            )
            if nombre_archivo and '.' in nombre_archivo:
                ext = nombre_archivo.rsplit('.', 1)[-1]
            else:
                ext = 'csv'
            importacion.archivo_csv.name = (
                f"importaciones/fallo_permiso_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
            )
            importacion.save()

        try:
            archivo.seek(0)
        except Exception:
            pass

        errores = []
        exitosos = 0
        total = 0

        try:
            nombre = nombre_normalizado

            if nombre.endswith('.xlsx'):
                import pandas as pd

                df = pd.read_excel(archivo, engine='openpyxl')
                df.columns = [clean_val(str(c)).lower() for c in df.columns]
                _validar_columnas_importacion(df.columns)
                rows = df.to_dict('records')

                for row_num, row in enumerate(rows, start=2):
                    if not any(clean_val(valor) for valor in row.values()):
                        continue
                    total += 1
                    try:
                        exitosos += _procesar_fila_comprobante(row, row_num, empresa)
                    except Exception as e:
                        errores.append(f"Fila {row_num}: Error inesperado: {str(e)}")

            else:
                archivo.seek(0)
                decoded_file = archivo.read().decode('utf-8-sig')
                primeras_lineas = decoded_file.split('\n')
                delimiter = ';'
                if primeras_lineas:
                    cabecera = primeras_lineas[0]
                    if ',' in cabecera and ';' not in cabecera:
                        delimiter = ','

                csv_file = io.StringIO(decoded_file)
                csv_reader = csv.DictReader(csv_file, delimiter=delimiter)

                if csv_reader.fieldnames:
                    csv_reader.fieldnames = [clean_val(name).lower() for name in csv_reader.fieldnames]
                _validar_columnas_importacion(csv_reader.fieldnames)

                for row_num, row in enumerate(csv_reader, start=2):
                    if not any(clean_val(valor) for valor in row.values()):
                        continue
                    total += 1
                    try:
                        exitosos += _procesar_fila_comprobante(row, row_num, empresa)
                    except Exception as e:
                        errores.append(f"Fila {row_num}: Error inesperado: {str(e)}")

            importacion.total_registros = total
            importacion.importados_exitosos = exitosos
            importacion.errores = len(errores)
            importacion.log_errores = '\n'.join(errores[:100])
            importacion.estado = 'COMPLETADO' if exitosos > 0 else 'ERROR'
            importacion.save()

            if errores:
                primer_error = errores[0][:200]
                messages.warning(
                    request,
                    f'Importación completada: {exitosos} exitosos, '
                    f'{len(errores)} errores. Primer error: {primer_error}'
                )
            else:
                messages.success(
                    request,
                    f'Importación completada: {exitosos} exitosos, {len(errores)} errores'
                )
        except Exception as e:
            importacion.estado = 'ERROR'
            importacion.log_errores = f"Error crítico al leer el archivo: {str(e)}"
            importacion.save()
            messages.error(request, f'Error en importación: {str(e)}')

        return redirect('comprobantes:lista')

    empresas = Empresa.objects.filter(activo=True)
    return render(request, 'comprobantes/importar.html', {
        'empresas': empresas,
        'empresa_default': empresas.first() if empresas.count() == 1 else None,
        'importaciones_recientes': ImportacionComprobante.objects.select_related(
            'usuario'
        )[:5],
    })


@login_required
def descargar_plantilla_importacion(request):
    """Descarga una plantilla CSV UTF-8 lista para completar."""
    contenido = (
        'tipo;serie;numero;fecha;cliente_tipo_doc;cliente_num_doc;cliente_nombre;'
        'producto_codigo;producto_descripcion;cantidad;precio_unitario;categoria;'
        'afectacion_igv;moneda;pais_codigo\n'
        '01;F001;1;2026-07-16;6;20123456789;EMPRESA DEMO SAC;PROD001;'
        'Producto gravado;2;100.00;GENERAL;10;PEN;PE\n'
    )
    response = HttpResponse('\ufeff' + contenido, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="plantilla_importacion.csv"'
    return response


@login_required
def buscar_empresas_ajax(request):
    q = request.GET.get('q', '')
    from django.db.models import Q
    empresas = Empresa.objects.filter(
        Q(razon_social__icontains=q) | Q(ruc__icontains=q) | Q(codigo__icontains=q)
    )
    data = [
        {'id': emp.id, 'codigo': emp.codigo, 'ruc': emp.ruc, 'razon_social': emp.razon_social}
        for emp in empresas[:20]
    ]
    return JsonResponse({'results': data})


@login_required
def buscar_clientes_ajax(request):
    q = request.GET.get('q', '')
    from django.db.models import Q
    clientes = Cliente.objects.filter(activo=True).filter(
        Q(razon_social__icontains=q) | Q(num_doc__icontains=q) | Q(codigo__icontains=q)
    )
    data = [
        {
            'id': cli.id, 'codigo': cli.codigo, 'num_doc': cli.num_doc,
            'razon_social': cli.razon_social, 'tipo_doc': cli.tipo_doc,
            'pais_codigo': cli.pais_codigo,
        }
        for cli in clientes[:20]
    ]
    return JsonResponse({'results': data})


@login_required
def buscar_productos_ajax(request):
    q = request.GET.get('q', '')
    afectacion = request.GET.get('afectacion', '')
    excluir_afectacion = request.GET.get('excluir_afectacion', '')
    from django.db.models import Q
    productos = Producto.objects.filter(activo=True).filter(
        Q(descripcion__icontains=q) | Q(codigo__icontains=q)
    )
    if afectacion:
        productos = productos.filter(cod_tipo_afectacion=afectacion)
    if excluir_afectacion:
        productos = productos.exclude(cod_tipo_afectacion=excluir_afectacion)
    productos = productos.order_by('codigo')
    data = [
        {'id': prod.id, 'codigo': prod.codigo, 'descripcion': prod.descripcion,
         'precio': str(prod.precio_unitario),
         'afectacion': prod.cod_tipo_afectacion}
        for prod in productos[:20]
    ]
    return JsonResponse({'results': data})
