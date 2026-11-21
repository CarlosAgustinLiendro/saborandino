from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import RegistroForm, AccesoForm, PerfilForm
from .models import Usuario
from .services import resolver_solicitud


class AccesoView(LoginView):
    template_name = "cuentas/login.html"
    authentication_form = AccesoForm
    redirect_authenticated_user = True


def registro(request):
    if request.user.is_authenticated:
        return redirect("inicio:home")
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error(
                None, "El usuario o correo ya fue registrado. Revisá los datos."
            )
        else:
            return redirect("cuentas:pendiente")
    return render(request, "cuentas/registro.html", {"form": form})


def pendiente(request):
    return render(request, "cuentas/pendiente.html")


from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.urls import reverse


def reestablecer_password(request):
    """Paso 1: Solicitar recuperación de contraseña vía correo electrónico seguro."""
    if request.user.is_authenticated:
        return redirect("inicio:home")

    error = None
    if request.method == "POST":
        identificador = request.POST.get("email", "").strip().lower()

        if not identificador:
            error = "Por favor, ingresá tu usuario o correo electrónico registrado."
        else:
            usuario = Usuario.objects.filter(
                Q(email__iexact=identificador) | Q(username__iexact=identificador)
            ).first()
            link_generado = None

            if usuario:
                token = default_token_generator.make_token(usuario)
                uidb64 = urlsafe_base64_encode(force_bytes(usuario.pk))
                reset_path = reverse(
                    "cuentas:reestablecer_confirmar",
                    kwargs={"uidb64": uidb64, "token": token},
                )
                link_generado = request.build_absolute_uri(reset_path)

                # Envío de correo electrónico con el enlace único de un solo uso
                asunto = "Recuperación de contraseña · Sabor Andino S.R.L."
                cuerpo = (
                    f"Hola {usuario.first_name or usuario.username},\n\n"
                    "Recibimos una solicitud para restablecer la contraseña de tu cuenta en el sistema de Sabor Andino S.R.L.\n\n"
                    f"Para definir tu nueva clave de acceso de forma segura, ingresá al siguiente enlace:\n{link_generado}\n\n"
                    "Este enlace es personal y de un solo uso. Si vos no solicitaste este cambio, podés ignorar este correo y tu cuenta continuará protegida.\n\n"
                    "Atentamente,\n"
                    "Equipo de Administración · Sabor Andino S.R.L."
                )
                try:
                    send_mail(
                        asunto,
                        cuerpo,
                        None,
                        [usuario.email],
                        fail_silently=True,
                    )
                except Exception:
                    pass

                # Guardamos el enlace en sesión para facilitar pruebas directas en entorno local
                request.session["demo_reset_link"] = link_generado
                request.session["demo_reset_email"] = usuario.email

            return redirect(f"{reverse('cuentas:reestablecer_enviado')}?email={identificador}")

    return render(request, "cuentas/reestablecer.html", {"error": error})

    return render(request, "cuentas/reestablecer.html", {"error": error})


def reestablecer_enviado(request):
    """Paso 2: Confirmación de envío de correo y recordatorio de seguridad."""
    email = request.GET.get("email", request.session.get("demo_reset_email", ""))
    demo_link = request.session.get("demo_reset_link")
    return render(
        request,
        "cuentas/reestablecer_enviado.html",
        {"email": email, "demo_link": demo_link},
    )


def reestablecer_confirmar(request, uidb64, token):
    """Paso 3: Verificación del token criptográfico y definición de la nueva contraseña."""
    if request.user.is_authenticated:
        return redirect("inicio:home")

    usuario = None
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        usuario = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        usuario = None

    if usuario is None or not default_token_generator.check_token(usuario, token):
        return render(request, "cuentas/reestablecer_invalido.html")

    error = None
    if request.method == "POST":
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        if not password1 or not password2:
            error = "Completá ambos campos de contraseña."
        elif password1 != password2:
            error = "Las contraseñas no coinciden. Por favor, verificalas."
        elif len(password1) < 10:
            error = "La nueva contraseña debe tener al menos 10 caracteres."
        else:
            usuario.set_password(password1)
            usuario.is_active = True
            usuario.estado = "aprobado"
            usuario.save()
            request.session.pop("demo_reset_link", None)
            request.session.pop("demo_reset_email", None)
            messages.success(
                request,
                "¡Contraseña actualizada con éxito! Ya podés iniciar sesión con tus nuevas credenciales.",
            )
            return redirect("cuentas:login")

    return render(
        request,
        "cuentas/reestablecer_confirmar.html",
        {"usuario": usuario, "error": error},
    )


@login_required
def solicitudes(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    return render(
        request,
        "cuentas/solicitudes.html",
        {
            "solicitudes": Usuario.objects.filter(estado="pendiente").order_by(
                "date_joined"
            )
        },
    )


@login_required
@require_POST
def resolver(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied
    get_object_or_404(Usuario, pk=pk)
    accion = request.POST.get("accion")
    if accion not in ("aprobar", "rechazar"):
        raise PermissionDenied
    changed = resolver_solicitud(
        usuario_id=pk, aprobar=accion == "aprobar", administrador=request.user
    )
    messages.success(
        request,
        "Solicitud resuelta." if changed else "La solicitud ya había sido resuelta.",
    )
    return redirect("cuentas:solicitudes")


@login_required
def perfil(request):
    usuario = request.user
    editando = request.GET.get("editar") == "1"
    if request.method == "POST":
        form = PerfilForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("cuentas:perfil")
        else:
            editando = True
    else:
        form = PerfilForm(instance=usuario)

    return render(
        request,
        "cuentas/perfil.html",
        {
            "form": form,
            "usuario": usuario,
            "editando": editando,
        },
    )


@login_required
def ajustes(request):
    return render(
        request,
        "cuentas/ajustes.html",
        {
            "usuario": request.user,
        },
    )


@login_required
def cambiar_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Tu contraseña fue actualizada correctamente.")
            return redirect("cuentas:ajustes")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "cuentas/cambiar_password.html", {"form": form})


@login_required
@require_POST
def eliminar_cuenta(request):
    usuario = request.user
    if usuario.is_superuser:
        messages.error(request, "No se puede eliminar la cuenta de administración principal.")
        return redirect("cuentas:ajustes")
    logout(request)
    usuario.delete()
    messages.success(request, "Tu cuenta ha sido eliminada con éxito.")
    return redirect("cuentas:login")
