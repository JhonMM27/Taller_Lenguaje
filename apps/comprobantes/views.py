from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from apps.comprobantes.models import Comprobante, SerieComprobante, ImportacionComprobante, DetalleComprobante
from apps.empresas.models import Empresa
from apps.clientes.models import Cliente
from apps.productos.models import Producto, CategoriaProducto
from datetime import datetime
import csv
import io


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


    context = {
        'comprobantes': comprobantes.order_by('-fecha', '-created_at')[:50],
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
    from apps.empresas.models import Empresa
    from apps.clientes.models import Cliente
    from apps.productos.models import Producto
    
    if request.method == 'POST':
        empresa_id = request.POST.get('empresa_id')
        cliente_id = request.POST.get('cliente_id')
        fecha = request.POST.get('fecha')
        tipo = request.POST.get('tipo')

        detalles_data = []
        producto_ids = request.POST.getlist('producto_id')
        cantidades = request.POST.getlist('cantidad')
        precios = request.POST.getlist('precio_unitario')

        for i, producto_id in enumerate(producto_ids):
            detalles_data.append({
                'producto_id': producto_id,
                'cantidad': cantidades[i],
                'precio_unitario': precios[i],
            })

        from apps.comprobantes.serializers import ComprobanteCreateSerializer
        serializer = ComprobanteCreateSerializer(data={
            'empresa_id': empresa_id,
            'cliente_id': cliente_id,
            'fecha': fecha,
            'tipo': tipo,
            'detalles': detalles_data,
        })
        if serializer.is_valid():
            serializer.save()
            return redirect('comprobantes:lista')
        
        empresas = Empresa.objects.all()
        clientes = Cliente.objects.all()
        productos = Producto.objects.all()
        return render(request, 'comprobantes/crear.html', {
            'errors': serializer.errors,
            'empresas': empresas,
            'clientes': clientes,
            'productos': productos,
            'today': datetime.now().strftime('%Y-%m-%d')
        })

    empresas = Empresa.objects.all()
    clientes = Cliente.objects.all()
    productos = Producto.objects.all()
    return render(request, 'comprobantes/crear.html', {
        'empresas': empresas,
        'clientes': clientes,
        'productos': productos,
        'today': datetime.now().strftime('%Y-%m-%d')
    })


@login_required
def detalle_comprobante(request, pk):
    comprobante = get_object_or_404(Comprobante.objects.select_related('cliente', 'empresa', 'serie'), pk=pk)
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
        # Intentar formatear el XML para que se vea "profesional"
        dom = xml.dom.minidom.parseString(comprobante.xml_firmado)
        pretty_xml = dom.toprettyxml(indent="  ")
        # Eliminar líneas vacías generadas por toprettyxml en algunos casos
        pretty_xml = "\n".join([line for line in pretty_xml.splitlines() if line.strip()])
    except Exception:
        # Si falla el parseo (ej: ya es muy complejo), devolver el original
        pretty_xml = comprobante.xml_firmado

    response = HttpResponse(pretty_xml.encode('utf-8'), content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="{comprobante.nombre_xml}"'
    return response


@login_required
def descargar_excel_comprobante(request, pk):
    comprobante = get_object_or_404(Comprobante.objects.select_related('cliente', 'empresa', 'serie'), pk=pk)
    import pandas as pd
    from io import BytesIO

    # Crear el buffer
    output = BytesIO()
    
    # Crear los datos para el reporte profesional
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
    
    # Usar ExcelWriter para un diseño profesional
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_detalles.to_excel(writer, sheet_name='Comprobante', startrow=10, index=False)
        
        workbook  = writer.book
        worksheet = writer.sheets['Comprobante']
        
        # Formatos
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#4F46E5', 'font_color': 'white', 'border': 1, 'align': 'center'})
        title_fmt = workbook.add_format({'bold': True, 'font_size': 18, 'font_color': '#1E293B'})
        subtitle_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#4F46E5'})
        data_fmt = workbook.add_format({'font_size': 10})
        num_fmt = workbook.add_format({'num_format': 'S/ #,##0.00', 'font_size': 10})
        
        # Título y Datos del Emisor
        worksheet.write('A1', f'{comprobante.get_tipo_display().upper()} ELECTRÓNICA', title_fmt)
        worksheet.write('A2', f'{comprobante.serie.serie}-{comprobante.numero:08d}', subtitle_fmt)
        
        worksheet.write('A4', 'EMISOR:', data_fmt)
        worksheet.write('B4', comprobante.empresa.razon_social, data_fmt)
        worksheet.write('A5', 'RUC:', data_fmt)
        worksheet.write('B5', comprobante.empresa.ruc, data_fmt)
        
        # Datos del Cliente
        worksheet.write('E4', 'CLIENTE:', data_fmt)
        worksheet.write('F4', comprobante.cliente.razon_social, data_fmt)
        worksheet.write('E5', 'DOC:', data_fmt)
        worksheet.write('F5', comprobante.cliente.num_doc, data_fmt)
        worksheet.write('E6', 'FECHA:', data_fmt)
        worksheet.write('F6', str(comprobante.fecha), data_fmt)

        # Aplicar formato de cabecera a la tabla
        for col_num, value in enumerate(df_detalles.columns.values):
            worksheet.write(10, col_num, value, header_fmt)
            
        # Ajustar anchos
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 40)
        worksheet.set_column('C:G', 12)
        
        # Totales
        row_total = 10 + len(df_detalles) + 2
        worksheet.write(row_total, 5, 'SUBTOTAL:', data_fmt)
        worksheet.write(row_total, 6, float(comprobante.subtotal), num_fmt)
        worksheet.write(row_total+1, 5, 'IGV (18%):', data_fmt)
        worksheet.write(row_total+1, 6, float(comprobante.igv), num_fmt)
        worksheet.write(row_total+2, 5, 'TOTAL:', subtitle_fmt)
        worksheet.write(row_total+2, 6, float(comprobante.total), num_fmt)

    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="Comprobante_{comprobante.serie.serie}_{comprobante.numero}.xlsx"'
    return response


@login_required
def reenviar_comprobante(request, pk):
    comprobante = get_object_or_404(Comprobante, pk=pk)

    if comprobante.estado != 'RECHAZADO':
        return HttpResponse("Solo se pueden reenviar comprobantes rechazados", status=400)

    from apps.sunat_ose.xml_generator import generar_xml_ubl, firmar_xml

    try:
        xml_content = generar_xml_ubl(comprobante)
        xml_firmado = firmar_xml(xml_content)
        comprobante.xml_firmado = xml_firmado.decode('utf-8') if isinstance(xml_firmado, bytes) else xml_firmado
        comprobante.estado = 'ENVIADO'
        comprobante.save(update_fields=['xml_firmado', 'estado'])
        return redirect('comprobantes:detalle', pk=pk)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


@login_required
def emitir_comprobante(request, pk):
    comprobante = get_object_or_404(Comprobante, pk=pk)

    if comprobante.estado != 'BORRADOR':
        return HttpResponse("Solo se pueden emitir comprobantes en estado BORRADOR", status=400)

    from apps.sunat_ose.xml_generator import generar_xml_ubl, firmar_xml

    try:
        xml_content = generar_xml_ubl(comprobante)
        xml_firmado = firmar_xml(xml_content)
        comprobante.xml_firmado = xml_firmado.decode('utf-8') if isinstance(xml_firmado, bytes) else xml_firmado
        comprobante.estado = 'EMITIDO'
        comprobante.save(update_fields=['xml_firmado', 'estado'])
        return redirect('comprobantes:detalle', pk=pk)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


@login_required
def importar_csv(request):
    if request.method == 'POST':
        archivo = request.FILES.get('archivo_csv')
        if not archivo:
            messages.error(request, 'No se seleccionó ningún archivo')
            return redirect('comprobantes:importar')

        importacion = ImportacionComprobante.objects.create(
            archivo_csv=archivo,
            usuario=request.user,
            estado='PROCESANDO'
        )

        errores = []
        exitosos = 0
        total = 0

        try:
            decoded_file = archivo.read().decode('utf-8-sig')
            csv_reader = csv.DictReader(io.StringIO(decoded_file), delimiter=';')
            
            for row_num, row in enumerate(csv_reader, start=2):
                total += 1
                try:
                    tipo = row.get('tipo', '01').strip()
                    serie = row.get('serie', '').strip()
                    numero = int(row.get('numero', '0').strip())
                    fecha_str = row.get('fecha', '').strip()
                    cliente_tipo_doc = row.get('cliente_tipo_doc', '6').strip()
                    cliente_num_doc = row.get('cliente_num_doc', '').strip()
                    cliente_nombre = row.get('cliente_nombre', 'Cliente Varios').strip()
                    producto_codigo = row.get('producto_codigo', '').strip()
                    cantidad = float(row.get('cantidad', '1').strip())
                    precio_unitario = float(row.get('precio_unitario', '0').strip())
                    categoria_nombre = row.get('categoria', '').strip()

                    if not serie or not cliente_num_doc:
                        errores.append(f"Fila {row_num}: Falta información obligatoria")
                        continue

                    cliente, _ = Cliente.objects.get_or_create(
                        tipo_doc=cliente_tipo_doc,
                        num_doc=cliente_num_doc,
                        defaults={'razon_social': cliente_nombre}
                    )

                    categoria = None
                    if categoria_nombre:
                        categoria, _ = CategoriaProducto.objects.get_or_create(
                            nombre__iexact=categoria_nombre,
                            defaults={'nombre': categoria_nombre}
                        )

                    producto, created = Producto.objects.get_or_create(
                        codigo=producto_codigo,
                        defaults={
                            'descripcion': producto_codigo,
                            'precio_unitario': precio_unitario,
                            'categoria': categoria,
                        }
                    )
                    if created:
                        producto.descripcion = row.get('producto_descripcion', producto_codigo)
                        producto.save()

                    empresa = Empresa.objects.first()
                    if not empresa:
                        errores.append(f"Fila {row_num}: No hay empresa configurada")
                        continue

                    serie_obj = SerieComprobante.objects.filter(
                        empresa=empresa,
                        serie=serie,
                        activa=True
                    ).first()
                    if not serie_obj:
                        errores.append(f"Fila {row_num}: Serie {serie} no existe o no está activa")
                        continue

                    existe = Comprobante.objects.filter(
                        serie=serie_obj,
                        numero=numero
                    ).exists()
                    if existe:
                        errores.append(f"Fila {row_num}: Comprobante {serie}-{numero:08d} ya existe")
                        continue

                    from datetime import datetime
                    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else datetime.now().date()

                    comprobante = Comprobante.objects.create(
                        empresa=empresa,
                        cliente=cliente,
                        serie=serie_obj,
                        numero=numero,
                        fecha=fecha,
                        tipo=tipo,
                        estado='BORRADOR'
                    )

                    DetalleComprobante.objects.create(
                        comprobante=comprobante,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                        afecto_igv=producto.afecto_igv,
                        cod_tipo_afectacion=producto.cod_tipo_afectacion,
                    )
                    comprobante.calcular_totales()
                    exitosos += 1

                except Exception as e:
                    errores.append(f"Fila {row_num}: {str(e)}")

            importacion.total_registros = total
            importacion.importados_exitosos = exitosos
            importacion.errores = len(errores)
            importacion.log_errores = '\n'.join(errores[:100])
            importacion.estado = 'COMPLETADO' if exitosos > 0 else 'ERROR'
            importacion.save()

            messages.success(request, f'Importación completada: {exitosos} exitosos, {len(errores)} errores')
        except Exception as e:
            importacion.estado = 'ERROR'
            importacion.log_errores = str(e)
            importacion.save()
            messages.error(request, f'Error en importación: {str(e)}')

        return redirect('comprobantes:lista')

    return render(request, 'comprobantes/importar.html')

@login_required
def buscar_empresas_ajax(request):
    q = request.GET.get('q', '')
    from django.db.models import Q
    empresas = Empresa.objects.filter(Q(razon_social__icontains=q) | Q(ruc__icontains=q) | Q(codigo__icontains=q))
    data = []
    for emp in empresas[:20]:
        data.append({
            'id': emp.id,
            'codigo': emp.codigo,
            'ruc': emp.ruc,
            'razon_social': emp.razon_social
        })
    from django.http import JsonResponse
    return JsonResponse({'results': data})

@login_required
def buscar_clientes_ajax(request):
    q = request.GET.get('q', '')
    from django.db.models import Q
    clientes = Cliente.objects.filter(Q(razon_social__icontains=q) | Q(num_doc__icontains=q) | Q(codigo__icontains=q))
    data = []
    for cli in clientes[:20]:
        data.append({
            'id': cli.id,
            'codigo': cli.codigo,
            'num_doc': cli.num_doc,
            'razon_social': cli.razon_social
        })
    from django.http import JsonResponse
    return JsonResponse({'results': data})

@login_required
def buscar_productos_ajax(request):
    q = request.GET.get('q', '')
    from django.db.models import Q
    productos = Producto.objects.filter(Q(descripcion__icontains=q) | Q(codigo__icontains=q))
    data = []
    for prod in productos[:20]:
        data.append({
            'id': prod.id,
            'codigo': prod.codigo,
            'descripcion': prod.descripcion,
            'precio': str(prod.precio_unitario)
        })
    from django.http import JsonResponse
    return JsonResponse({'results': data})