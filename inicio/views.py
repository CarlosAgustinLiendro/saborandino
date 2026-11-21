from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from cuentas.models import Usuario
from acopio.models import ComprobanteAcopio, Anticipo, Productor, Liquidacion


@login_required
def home(request):
    """
    Panel Principal de Trabajo: Sistema de Recepción y Liquidaciones (P02 y P04)
    Enfocado estrictamente en los módulos y procesos aprobados en el informe técnico.
    """
    kilos_acopiados = ComprobanteAcopio.objects.aggregate(total=Sum("kilos_netos"))["total"] or 0
    total_anticipos = Anticipo.objects.aggregate(total=Sum("importe"))["total"] or 0
    total_liquidado = Liquidacion.objects.aggregate(total=Sum("saldo_neto"))["total"] or 0

    return render(
        request,
        "inicio/home.html",
        {
            "recepciones_count": ComprobanteAcopio.objects.count(),
            "kilos_acopiados": kilos_acopiados,
            "total_anticipos": total_anticipos,
            "total_liquidado": total_liquidado,
            "productores_count": Productor.objects.count(),
            "liquidaciones_count": Liquidacion.objects.count(),
            "pendientes": (
                Usuario.objects.filter(estado="pendiente").count()
                if request.user.is_superuser
                else None
            ),
            "recepciones_recientes": ComprobanteAcopio.objects.select_related(
                "productor", "tipo_producto", "campania"
            ).order_by("-fecha", "-id")[:5],
            "anticipos_recientes": Anticipo.objects.select_related("productor").order_by(
                "-fecha", "-id"
            )[:5],
            "liquidaciones_recientes": Liquidacion.objects.select_related(
                "comprobante__productor", "comprobante__tipo_producto"
            ).order_by("-fecha_liquidacion", "-id")[:5],
        },
    )


def salud(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"estado": "no disponible"}, status=503)
    return JsonResponse({"estado": "ok"})



def salud(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"estado": "no disponible"}, status=503)
    return JsonResponse({"estado": "ok"})
