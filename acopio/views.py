import csv
from datetime import timedelta
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import (
    ComprobanteAcopioForm,
    AnticipoForm,
    PrecioReferenciaForm,
    ProductorForm,
    RectificacionForm,
)
from .models import (
    ComprobanteAcopio,
    Anticipo,
    Liquidacion,
    PrecioReferencia,
    Productor,
    Campania,
    TipoMateriaPrima,
    HistorialActividad,
    registrar_historial,
)


# ==============================================================================
# PROCESO 2: RECEPCIÓN Y PESAJE (Cachi) - HU-01, HU-02, HU-06, HU-07
# ==============================================================================

@login_required
def recepciones_lista(request):
    """Consulta de comprobantes de acopio con filtros por productor, fecha y campaña (HU-06)."""
    qs = ComprobanteAcopio.objects.select_related(
        "productor", "tipo_producto", "campania", "usuario_responsable"
    ).all()

    q = request.GET.get("q", "").strip()
    fecha = request.GET.get("fecha", "").strip()
    campania_id = request.GET.get("campania", "").strip()

    if q:
        qs = qs.filter(
            Q(productor__nombre_completo__icontains=q)
            | Q(numero__icontains=q)
            | Q(procedencia__icontains=q)
        )
    if fecha:
        qs = qs.filter(fecha=fecha)
    if campania_id:
        qs = qs.filter(campania_id=campania_id)

    total_kilos = qs.aggregate(total=Sum("kilos_netos"))["total"] or 0

    return render(
        request,
        "acopio/recepciones_lista.html",
        {
            "comprobantes": qs,
            "total_kilos": total_kilos,
            "campanias": Campania.objects.all(),
            "campania_actual": campania_id,
        },
    )


@login_required
def recepcion_crear(request):
    """Carga de pesaje, cálculo de kilos netos y emisión de comprobante (HU-01, HU-02)."""
    if request.method == "POST":
        form = ComprobanteAcopioForm(request.POST)
        if form.is_valid():
            comprobante = form.save(commit=False)
            comprobante.usuario_responsable = request.user

            # Obtener precio de referencia vigente para la campaña y producto (HU-03)
            precio_ref = PrecioReferencia.objects.filter(
                tipo_producto=comprobante.tipo_producto,
                campania=comprobante.campania,
            ).first()
            comprobante.precio_referencia = (
                precio_ref.precio_por_kg if precio_ref else Decimal("2500.00")
            )

            # Soporte de contingencia offline en Cachi
            if request.POST.get("origen_offline") == "1":
                comprobante.origen_offline = True

            # Generar número correlativo único (HU-02)
            ultimo = ComprobanteAcopio.objects.order_by("-id").first()
            correlativo = (ultimo.id + 1) if ultimo else 1
            comprobante.numero = f"REC-2026-{correlativo:03d}"

            comprobante.save()

            registrar_historial(
                request.user,
                "RECEPCION_CREAR",
                "Recepción y Pesaje",
                f"Comprobante {comprobante.numero} emitido para {comprobante.productor.nombre_completo} ({comprobante.kilos_netos} kg de {comprobante.tipo_producto.nombre})",
                comprobante.numero,
            )

            messages.success(
                request,
                f"Comprobante {comprobante.numero} emitido correctamente para {comprobante.productor.nombre_completo}.",
            )
            return redirect("acopio:recepcion_detalle", pk=comprobante.pk)
    else:
        form = ComprobanteAcopioForm(initial={"fecha": timezone.now().date(), "procedencia": "Cachi, Salta"})

    return render(request, "acopio/recepcion_form.html", {"form": form})


@login_required
def recepcion_detalle(request, pk):
    """Visualización e impresión de comprobante oficial de acopio (HU-02)."""
    comprobante = get_object_or_404(
        ComprobanteAcopio.objects.select_related(
            "productor", "tipo_producto", "campania", "usuario_responsable"
        ),
        pk=pk,
    )
    tiene_liquidacion = hasattr(comprobante, "liquidacion")
    return render(
        request,
        "acopio/recepcion_detalle.html",
        {"comprobante": comprobante, "tiene_liquidacion": tiene_liquidacion},
    )


@login_required
def recepcion_rectificar(request, pk):
    """Rectificación autorizada de comprobante de acopio sin borrado silencioso (pág. 8 y 14 del informe)."""
    if not request.user.is_superuser:
        raise PermissionDenied("Solo el Socio Gerente o Administración pueden autorizar la rectificación de comprobantes.")

    comprobante = get_object_or_404(ComprobanteAcopio, pk=pk)
    if request.method == "POST":
        form = RectificacionForm(request.POST, instance=comprobante)
        if form.is_valid():
            anterior = f"Bruto: {comprobante.kilos_brutos} kg, Tara: {comprobante.tara} kg, Netos: {comprobante.kilos_netos} kg, Humedad: {comprobante.porcentaje_humedad}%"
            rect = form.save(commit=False)
            rect.rectificado = True
            rect.save()
            nuevo = f"Bruto: {rect.kilos_brutos} kg, Tara: {rect.tara} kg, Netos: {rect.kilos_netos} kg, Humedad: {rect.porcentaje_humedad}%"

            # Si ya tenía liquidación, recalcular bruto y saldo
            if hasattr(rect, "liquidacion"):
                liq = rect.liquidacion
                liq.importe_bruto = rect.kilos_netos * rect.precio_referencia
                liq.saldo_neto = max(Decimal("0.00"), liq.importe_bruto - liq.total_anticipos)
                liq.save()

            registrar_historial(
                request.user,
                "RECEPCION_RECTIFICAR",
                "Recepción y Pesaje",
                f"Rectificación de comprobante {rect.numero}. Motivo: {rect.motivo_rectificacion}. Antes: [{anterior}] -> Ahora: [{nuevo}]",
                rect.numero,
            )
            messages.success(request, f"Comprobante {rect.numero} rectificado correctamente con registro en el historial de auditoría.")
            return redirect("acopio:recepcion_detalle", pk=rect.pk)
    else:
        form = RectificacionForm(instance=comprobante)

    return render(request, "acopio/recepcion_rectificar.html", {"form": form, "comprobante": comprobante})


# ==============================================================================
# PROCESO 4: ANTICIPOS EN EFECTIVO (HU-04)
# ==============================================================================

@login_required
def anticipos_lista(request):
    """Consulta de anticipos registrados por productor y estado de imputación (HU-04)."""
    qs = Anticipo.objects.select_related("productor", "usuario_registro").all()
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(productor__nombre_completo__icontains=q) | Q(numero__icontains=q)
        )

    total_anticipos = qs.aggregate(total=Sum("importe"))["total"] or 0
    return render(
        request,
        "acopio/anticipos_lista.html",
        {"anticipos": qs, "total_anticipos": total_anticipos},
    )


@login_required
def anticipo_crear(request):
    """Registro de anticipo en efectivo a productor (HU-04)."""
    if request.method == "POST":
        form = AnticipoForm(request.POST)
        if form.is_valid():
            anticipo = form.save(commit=False)
            anticipo.usuario_registro = request.user
            ultimo = Anticipo.objects.order_by("-id").first()
            correlativo = (ultimo.id + 1) if ultimo else 1
            anticipo.numero = f"ANT-2026-{correlativo:03d}"
            anticipo.save()

            registrar_historial(
                request.user,
                "ANTICIPO_REGISTRAR",
                "Anticipos",
                f"Anticipo {anticipo.numero} por ${anticipo.importe} registrado para {anticipo.productor.nombre_completo} (Autorizado por: {anticipo.autorizado_por})",
                anticipo.numero,
            )

            messages.success(
                request,
                f"Anticipo {anticipo.numero} por ${anticipo.importe} registrado exitosamente para {anticipo.productor.nombre_completo}.",
            )
            return redirect("acopio:anticipos_lista")
    else:
        initial = {"fecha": timezone.now().date()}
        productor_id = request.GET.get("productor")
        if productor_id:
            initial["productor"] = productor_id
        form = AnticipoForm(initial=initial)

    return render(request, "acopio/anticipo_form.html", {"form": form})


# ==============================================================================
# PROCESO 4: LIQUIDACIONES A PRODUCTORES (HU-05)
# ==============================================================================

@login_required
def liquidaciones_lista(request):
    """Listado de liquidaciones emitidas a productores."""
    liquidaciones = Liquidacion.objects.select_related(
        "comprobante__productor", "comprobante__tipo_producto", "usuario_responsable"
    ).all()
    return render(
        request, "acopio/liquidaciones_lista.html", {"liquidaciones": liquidaciones}
    )


@login_required
def liquidacion_generar(request, comprobante_id):
    """
    Genera la liquidación para un comprobante de acopio (HU-05):
    - Bruto = kilos netos * precio de referencia
    - Descuenta anticipos no imputados del productor (sin duplicar)
    - Vencimiento = recepción + 30 días corridos
    """
    comprobante = get_object_or_404(ComprobanteAcopio, pk=comprobante_id)

    if hasattr(comprobante, "liquidacion"):
        messages.info(request, "Este comprobante ya cuenta con una liquidación generada.")
        return redirect("acopio:liquidacion_detalle", pk=comprobante.liquidacion.pk)

    with transaction.atomic():
        # 1. Calcular importe bruto
        importe_bruto = comprobante.kilos_netos * comprobante.precio_referencia

        # 2. Buscar anticipos del productor pendientes de imputar (sin duplicar)
        anticipos_pendientes = Anticipo.objects.filter(
            productor=comprobante.productor, imputado=False
        )
        total_anticipos = sum(a.importe for a in anticipos_pendientes)

        # 3. Saldo neto a pagar
        saldo_neto = max(Decimal("0.00"), importe_bruto - total_anticipos)

        # 4. Vencimiento a 30 días corridos desde la fecha de recepción (HU-05)
        fecha_vencimiento = comprobante.fecha + timedelta(days=30)

        ultimo = Liquidacion.objects.order_by("-id").first()
        correlativo = (ultimo.id + 1) if ultimo else 1
        num_liq = f"LIQ-2026-{correlativo:03d}"

        liquidacion = Liquidacion.objects.create(
            numero=num_liq,
            comprobante=comprobante,
            fecha_liquidacion=timezone.now().date(),
            fecha_vencimiento=fecha_vencimiento,
            importe_bruto=importe_bruto,
            total_anticipos=total_anticipos,
            saldo_neto=saldo_neto,
            usuario_responsable=request.user,
            estado="Liquidado",
        )

        # Imputar anticipos aplicados para no descontarlos nuevamente
        if anticipos_pendientes.exists():
            liquidacion.anticipos_aplicados.set(anticipos_pendientes)
            anticipos_pendientes.update(imputado=True)

        registrar_historial(
            request.user,
            "LIQUIDACION_EMITIR",
            "Liquidaciones",
            f"Liquidación {liquidacion.numero} emitida para {comprobante.productor.nombre_completo}. Bruto: ${liquidacion.importe_bruto}, Anticipos: ${liquidacion.total_anticipos}, Neto: ${liquidacion.saldo_neto}, Vence: {fecha_vencimiento.strftime('%d/%m/%Y')}",
            liquidacion.numero,
        )

        messages.success(
            request,
            f"Liquidación {liquidacion.numero} generada con vencimiento el {fecha_vencimiento.strftime('%d/%m/%Y')}.",
        )
        return redirect("acopio:liquidacion_detalle", pk=liquidacion.pk)


@login_required
def liquidacion_detalle(request, pk):
    """Muestra el comprobante interno de liquidación listo para imprimir (HU-05)."""
    liquidacion = get_object_or_404(
        Liquidacion.objects.select_related(
            "comprobante__productor", "comprobante__tipo_producto", "comprobante__campania", "usuario_responsable"
        ).prefetch_related("anticipos_aplicados"),
        pk=pk,
    )
    return render(request, "acopio/liquidacion_detalle.html", {"liquidacion": liquidacion})


# ==============================================================================
# GESTIÓN DE PRECIOS DE REFERENCIA (Socio Gerente) - HU-03
# ==============================================================================

@login_required
def precios_lista(request):
    """Consulta de precios de referencia fijados por campaña (HU-03)."""
    precios = PrecioReferencia.objects.select_related(
        "tipo_producto", "campania", "fijado_por"
    ).all()
    return render(
        request,
        "acopio/precios_lista.html",
        {"precios": precios, "es_gerente": request.user.is_superuser},
    )


@login_required
def precio_guardar(request, pk=None):
    """Solo el Socio Gerente / Administrador puede fijar o modificar precios (HU-03)."""
    if not request.user.is_superuser:
        raise PermissionDenied("Solo el Socio Gerente puede modificar los precios de referencia.")

    instancia = get_object_or_404(PrecioReferencia, pk=pk) if pk else None
    if request.method == "POST":
        form = PrecioReferenciaForm(request.POST, instance=instancia)
        if form.is_valid():
            precio = form.save(commit=False)
            precio.fijado_por = request.user
            precio.save()

            registrar_historial(
                request.user,
                "PRECIO_MODIFICAR",
                "Precios de Referencia",
                f"Precio de referencia fijado para {precio.tipo_producto.nombre} ({precio.campania.nombre}): ${precio.precio_por_kg}/kg",
                f"{precio.tipo_producto.nombre} - {precio.campania.nombre}",
            )

            messages.success(request, f"Precio de referencia para {precio.tipo_producto} actualizado a ${precio.precio_por_kg}/kg.")
            return redirect("acopio:precios_lista")
    else:
        form = PrecioReferenciaForm(instance=instancia)

    return render(request, "acopio/precio_form.html", {"form": form, "instancia": instancia})


# ==============================================================================
# PADRÓN Y FICHA INTEGRAL DE PRODUCTORES (Módulo 2)
# ==============================================================================

@login_required
def productores_lista(request):
    """Padrón de los 47 productores agrícolas de los Valles Calchaquíes."""
    productores = Productor.objects.all()
    q = request.GET.get("q", "").strip()
    if q:
        productores = productores.filter(
            Q(nombre_completo__icontains=q) | Q(localidad__icontains=q) | Q(cuit__icontains=q)
        )
    return render(request, "acopio/productores_lista.html", {"productores": productores, "q": q})


@login_required
def productor_crear(request):
    """Alta de nuevo productor agrícola."""
    if request.method == "POST":
        form = ProductorForm(request.POST)
        if form.is_valid():
            productor = form.save()
            registrar_historial(
                request.user,
                "PRODUCTOR_ACTUALIZAR",
                "Padrón de Productores",
                f"Alta de nuevo productor: {productor.nombre_completo} ({productor.localidad}) - CUIT: {productor.cuit}",
                f"PROD-{productor.id}",
            )
            messages.success(request, f"Productor {productor.nombre_completo} registrado en el padrón.")
            return redirect("acopio:productor_detalle", pk=productor.pk)
    else:
        form = ProductorForm()

    return render(request, "acopio/productor_form.html", {"form": form, "titulo": "Nuevo Productor Agrícola"})


@login_required
def productor_editar(request, pk):
    """Modificación de datos de productor."""
    productor = get_object_or_404(Productor, pk=pk)
    if request.method == "POST":
        form = ProductorForm(request.POST, instance=productor)
        if form.is_valid():
            productor = form.save()
            registrar_historial(
                request.user,
                "PRODUCTOR_ACTUALIZAR",
                "Padrón de Productores",
                f"Modificación de productor: {productor.nombre_completo} ({productor.localidad})",
                f"PROD-{productor.id}",
            )
            messages.success(request, f"Datos de {productor.nombre_completo} actualizados.")
            return redirect("acopio:productor_detalle", pk=productor.pk)
    else:
        form = ProductorForm(instance=productor)

    return render(request, "acopio/productor_form.html", {"form": form, "productor": productor, "titulo": f"Editar Productor · {productor.nombre_completo}"})


@login_required
def productor_detalle(request, pk):
    """
    Ficha integral del productor:
    Relaciona al productor con sus comprobantes de acopio, anticipos y liquidaciones,
    mostrando el balance general consolidado.
    """
    productor = get_object_or_404(Productor, pk=pk)
    recepciones = ComprobanteAcopio.objects.filter(productor=productor).select_related(
        "tipo_producto", "campania"
    ).order_by("-fecha", "-id")
    anticipos = Anticipo.objects.filter(productor=productor).select_related("usuario_registro").order_by("-fecha", "-id")
    liquidaciones = Liquidacion.objects.filter(comprobante__productor=productor).select_related("comprobante").order_by("-fecha_liquidacion", "-id")

    total_kilos = recepciones.aggregate(total=Sum("kilos_netos"))["total"] or Decimal("0.00")
    total_anticipos = anticipos.aggregate(total=Sum("importe"))["total"] or Decimal("0.00")
    anticipos_pendientes = anticipos.filter(imputado=False).aggregate(total=Sum("importe"))["total"] or Decimal("0.00")
    total_liquidado_bruto = liquidaciones.aggregate(total=Sum("importe_bruto"))["total"] or Decimal("0.00")
    saldo_neto_liquidado = liquidaciones.aggregate(total=Sum("saldo_neto"))["total"] or Decimal("0.00")

    return render(
        request,
        "acopio/productor_detalle.html",
        {
            "productor": productor,
            "recepciones": recepciones,
            "anticipos": anticipos,
            "liquidaciones": liquidaciones,
            "total_kilos": total_kilos,
            "total_anticipos": total_anticipos,
            "anticipos_pendientes": anticipos_pendientes,
            "total_liquidado_bruto": total_liquidado_bruto,
            "saldo_neto_liquidado": saldo_neto_liquidado,
        },
    )


# ==============================================================================
# MÓDULO DE CONSULTAS Y REPORTES CON EXPORTACIÓN CSV (Módulo 6)
# ==============================================================================

@login_required
def reportes(request):
    """
    Módulo de Consultas y Reportes:
    Permite filtrar comprobantes, anticipos y liquidaciones por productor, campaña,
    materia prima y fechas, mostrando resúmenes y facilitando la exportación a CSV.
    """
    productor_id = request.GET.get("productor", "").strip()
    campania_id = request.GET.get("campania", "").strip()
    materia_id = request.GET.get("materia", "").strip()
    fecha_desde = request.GET.get("fecha_desde", "").strip()
    fecha_hasta = request.GET.get("fecha_hasta", "").strip()

    qs_rec = ComprobanteAcopio.objects.select_related("productor", "tipo_producto", "campania").all()
    qs_ant = Anticipo.objects.select_related("productor", "usuario_registro").all()
    qs_liq = Liquidacion.objects.select_related("comprobante__productor", "comprobante__tipo_producto", "comprobante__campania").all()

    if productor_id:
        qs_rec = qs_rec.filter(productor_id=productor_id)
        qs_ant = qs_ant.filter(productor_id=productor_id)
        qs_liq = qs_liq.filter(comprobante__productor_id=productor_id)

    if campania_id:
        qs_rec = qs_rec.filter(campania_id=campania_id)
        qs_liq = qs_liq.filter(comprobante__campania_id=campania_id)

    if materia_id:
        qs_rec = qs_rec.filter(tipo_producto_id=materia_id)
        qs_liq = qs_liq.filter(comprobante__tipo_producto_id=materia_id)

    if fecha_desde:
        qs_rec = qs_rec.filter(fecha__gte=fecha_desde)
        qs_ant = qs_ant.filter(fecha__gte=fecha_desde)
        qs_liq = qs_liq.filter(fecha_liquidacion__gte=fecha_desde)

    if fecha_hasta:
        qs_rec = qs_rec.filter(fecha__lte=fecha_hasta)
        qs_ant = qs_ant.filter(fecha__lte=fecha_hasta)
        qs_liq = qs_liq.filter(fecha_liquidacion__lte=fecha_hasta)

    total_kilos = qs_rec.aggregate(total=Sum("kilos_netos"))["total"] or Decimal("0.00")
    total_anticipos = qs_ant.aggregate(total=Sum("importe"))["total"] or Decimal("0.00")
    total_bruto = qs_liq.aggregate(total=Sum("importe_bruto"))["total"] or Decimal("0.00")
    total_saldo_neto = qs_liq.aggregate(total=Sum("saldo_neto"))["total"] or Decimal("0.00")

    return render(
        request,
        "acopio/reportes.html",
        {
            "productores": Productor.objects.all(),
            "campanias": Campania.objects.all(),
            "materias": TipoMateriaPrima.objects.all(),
            "filtro_productor": productor_id,
            "filtro_campania": campania_id,
            "filtro_materia": materia_id,
            "filtro_fecha_desde": fecha_desde,
            "filtro_fecha_hasta": fecha_hasta,
            "recepciones": qs_rec[:50],
            "anticipos": qs_ant[:50],
            "liquidaciones": qs_liq[:50],
            "total_kilos": total_kilos,
            "total_anticipos": total_anticipos,
            "total_bruto": total_bruto,
            "total_saldo_neto": total_saldo_neto,
        },
    )


@login_required
def reportes_exportar_csv(request):
    """
    Exportación de consultas a archivo CSV con codificación UTF-8 con BOM
    para visualización perfecta en Microsoft Excel y software de gestión.
    Cumple el caso de prueba de aceptación de la pág. 15 del informe.
    """
    tipo = request.GET.get("tipo", "recepciones")
    productor_id = request.GET.get("productor", "").strip()
    campania_id = request.GET.get("campania", "").strip()
    materia_id = request.GET.get("materia", "").strip()
    fecha_desde = request.GET.get("fecha_desde", "").strip()
    fecha_hasta = request.GET.get("fecha_hasta", "").strip()

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response.write("\ufeff")  # BOM UTF-8 para Excel

    if tipo == "anticipos":
        response["Content-Disposition"] = 'attachment; filename="anticipos_sabor_andino.csv"'
        writer = csv.writer(response, delimiter=";")
        writer.writerow(["Número", "Fecha", "Productor", "CUIT", "Importe ($)", "Autorizado Por", "Registrado Por", "Imputado a Liquidación"])
        qs = Anticipo.objects.select_related("productor", "usuario_registro").all()
        if productor_id:
            qs = qs.filter(productor_id=productor_id)
        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        for a in qs:
            writer.writerow([
                a.numero,
                a.fecha.strftime("%d/%m/%Y"),
                a.productor.nombre_completo,
                a.productor.cuit,
                f"{a.importe:.2f}",
                a.autorizado_por,
                a.usuario_registro.get_full_name() or a.usuario_registro.username,
                "Sí" if a.imputado else "Pendiente",
            ])
        return response

    elif tipo == "liquidaciones":
        response["Content-Disposition"] = 'attachment; filename="liquidaciones_sabor_andino.csv"'
        writer = csv.writer(response, delimiter=";")
        writer.writerow(["Número", "Fecha Emisión", "Vencimiento (30 días)", "Productor", "CUIT", "Comprobante Acopio", "Kilos Netos", "Importe Bruto ($)", "Anticipos Imputados ($)", "Saldo Neto a Pagar ($)", "Estado"])
        qs = Liquidacion.objects.select_related("comprobante__productor", "comprobante__tipo_producto", "comprobante__campania").all()
        if productor_id:
            qs = qs.filter(comprobante__productor_id=productor_id)
        if campania_id:
            qs = qs.filter(comprobante__campania_id=campania_id)
        if materia_id:
            qs = qs.filter(comprobante__tipo_producto_id=materia_id)
        if fecha_desde:
            qs = qs.filter(fecha_liquidacion__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha_liquidacion__lte=fecha_hasta)
        for l in qs:
            writer.writerow([
                l.numero,
                l.fecha_liquidacion.strftime("%d/%m/%Y"),
                l.fecha_vencimiento.strftime("%d/%m/%Y"),
                l.comprobante.productor.nombre_completo,
                l.comprobante.productor.cuit,
                l.comprobante.numero,
                f"{l.comprobante.kilos_netos:.2f}",
                f"{l.importe_bruto:.2f}",
                f"{l.total_anticipos:.2f}",
                f"{l.saldo_neto:.2f}",
                l.estado,
            ])
        return response

    else:
        # Por defecto: Recepciones de Acopio
        response["Content-Disposition"] = 'attachment; filename="recepciones_acopio_sabor_andino.csv"'
        writer = csv.writer(response, delimiter=";")
        writer.writerow(["Comprobante", "Fecha", "Productor", "CUIT", "Localidad", "Materia Prima", "Campaña", "Kilos Brutos", "Tara (kg)", "Kilos Netos", "Humedad (%)", "Precio Ref ($/kg)", "Importe Ref ($)", "Estado", "Rectificado"])
        qs = ComprobanteAcopio.objects.select_related("productor", "tipo_producto", "campania").all()
        if productor_id:
            qs = qs.filter(productor_id=productor_id)
        if campania_id:
            qs = qs.filter(campania_id=campania_id)
        if materia_id:
            qs = qs.filter(tipo_producto_id=materia_id)
        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        for r in qs:
            imp_ref = (r.kilos_netos or 0) * (r.precio_referencia or 0)
            writer.writerow([
                r.numero,
                r.fecha.strftime("%d/%m/%Y"),
                r.productor.nombre_completo,
                r.productor.cuit,
                r.procedencia,
                r.tipo_producto.nombre,
                r.campania.nombre,
                f"{r.kilos_brutos:.2f}",
                f"{r.tara:.2f}",
                f"{r.kilos_netos:.2f}",
                f"{r.porcentaje_humedad:.1f}%",
                f"{r.precio_referencia:.2f}",
                f"{imp_ref:.2f}",
                "Liquidado" if hasattr(r, "liquidacion") else "Pendiente",
                "Sí (Rectificado)" if r.rectificado else "Original",
            ])
        return response


# ==============================================================================
# HISTORIAL DE ACTIVIDADES / AUDITORÍA (Pág. 14 del informe)
# ==============================================================================

@login_required
def historial_actividades(request):
    """
    Consulta de auditoría y trazabilidad de actividades:
    - Creación de comprobantes
    - Rectificaciones autorizadas
    - Cambios en precios de referencia
    - Anticipos y liquidaciones emitidas
    """
    if not (request.user.is_superuser or request.user.is_staff):
        raise PermissionDenied("Acceso restringido a Socio Gerente y Administración.")

    qs = HistorialActividad.objects.select_related("usuario").all()
    modulo = request.GET.get("modulo", "").strip()
    if modulo:
        qs = qs.filter(modulo=modulo)

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(descripcion__icontains=q)
            | Q(comprobante_relacionado__icontains=q)
            | Q(usuario__username__icontains=q)
        )

    return render(
        request,
        "acopio/historial.html",
        {
            "eventos": qs[:100],
            "total_eventos": qs.count(),
            "modulo_actual": modulo,
        },
    )

