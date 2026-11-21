from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

app_name = "cuentas"
urlpatterns = [
    path("ingresar/", views.AccesoView.as_view(), name="login"),
    path("salir/", LogoutView.as_view(), name="logout"),
    path("registrarse/", views.registro, name="registro"),
    path("reestablecer/", views.reestablecer_password, name="reestablecer"),
    path("reestablecer/enviado/", views.reestablecer_enviado, name="reestablecer_enviado"),
    path(
        "reestablecer/confirmar/<str:uidb64>/<str:token>/",
        views.reestablecer_confirmar,
        name="reestablecer_confirmar",
    ),
    path("pendiente/", views.pendiente, name="pendiente"),
    path("perfil/", views.perfil, name="perfil"),
    path("ajustes/", views.ajustes, name="ajustes"),
    path("cambiar-password/", views.cambiar_password, name="cambiar_password"),
    path("eliminar-cuenta/", views.eliminar_cuenta, name="eliminar_cuenta"),
    path("solicitudes/", views.solicitudes, name="solicitudes"),
    path("solicitudes/<int:pk>/resolver/", views.resolver, name="resolver"),
]
