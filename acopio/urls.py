from django.urls import path
from . import views

app_name = "acopio"

urlpatterns = [
    # Proceso 2: Recepción y Pesaje
    path("recepciones/", views.recepciones_lista, name="recepciones_lista"),
    path("recepciones/nueva/", views.recepcion_crear, name="recepcion_crear"),
    path("recepciones/<int:pk>/", views.recepcion_detalle, name="recepcion_detalle"),
    path("recepciones/<int:pk>/rectificar/", views.recepcion_rectificar, name="recepcion_rectificar"),

    # Proceso 4: Anticipos
    path("anticipos/", views.anticipos_lista, name="anticipos_lista"),
    path("anticipos/nuevo/", views.anticipo_crear, name="anticipo_crear"),

    # Proceso 4: Liquidaciones
    path("liquidaciones/", views.liquidaciones_lista, name="liquidaciones_lista"),
    path("liquidaciones/generar/<int:comprobante_id>/", views.liquidacion_generar, name="liquidacion_generar"),
    path("liquidaciones/<int:pk>/", views.liquidacion_detalle, name="liquidacion_detalle"),

    # Precios de Referencia (Socio Gerente)
    path("precios/", views.precios_lista, name="precios_lista"),
    path("precios/nuevo/", views.precio_guardar, name="precio_crear"),
    path("precios/<int:pk>/editar/", views.precio_guardar, name="precio_editar"),

    # Padrón y Ficha de Productores
    path("productores/", views.productores_lista, name="productores_lista"),
    path("productores/nuevo/", views.productor_crear, name="productor_crear"),
    path("productores/<int:pk>/", views.productor_detalle, name="productor_detalle"),
    path("productores/<int:pk>/editar/", views.productor_editar, name="productor_editar"),

    # Consultas, Reportes y Exportación CSV
    path("reportes/", views.reportes, name="reportes"),
    path("reportes/exportar/csv/", views.reportes_exportar_csv, name="reportes_exportar_csv"),

    # Historial de Actividades / Auditoría
    path("historial/", views.historial_actividades, name="historial"),
]
