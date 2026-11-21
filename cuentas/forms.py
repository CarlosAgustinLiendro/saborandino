from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario


class RegistroForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ("username", "first_name", "last_name", "email")
        labels = {
            "username": "Nombre de usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo electrónico",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "Ej. Carlos Agustín", "class": "input-redondeado"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Ej. Liendro", "class": "input-redondeado"}),
            "username": forms.TextInput(attrs={"placeholder": "Ej. carlos.liendro", "class": "input-redondeado"}),
            "email": forms.EmailInput(attrs={"placeholder": "Ej. carlos@saborandino.com", "class": "input-redondeado"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "password1" in self.fields:
            self.fields["password1"].widget.attrs.update({
                "placeholder": "Ingrese su contraseña (mínimo 10 caracteres)",
                "class": "input-redondeado",
            })
        if "password2" in self.fields:
            self.fields["password2"].widget.attrs.update({
                "placeholder": "Repita su contraseña",
                "class": "input-redondeado",
            })

    def clean_username(self):
        value = self.cleaned_data["username"].strip().lower()
        if Usuario.objects.filter(username__iexact=value).exists():
            raise forms.ValidationError("Ese nombre de usuario ya está en uso.")
        return value

    def clean_email(self):
        value = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=value).exists():
            raise forms.ValidationError(
                "Ese correo ya está registrado. Contactá al administrador."
            )
        return value

    def save(self, commit=True):
        user = super().save(commit=False)
        # Solo se aceptan los campos del formulario; nunca privilegios enviados por el navegador.
        user.is_active = False
        user.estado = Usuario.Estado.PENDIENTE
        if commit:
            user.save()
        return user


class AccesoForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "No pudimos iniciar sesión. Revisá tus datos o consultá si tu cuenta fue aprobada.",
        "inactive": "La cuenta no está habilitada. Contactá al administrador.",
    }

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ("first_name", "last_name", "avatar")
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
            "avatar": "Avatar",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "Tu nombre", "class": "form-control"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Tu apellido", "class": "form-control"}),
            "avatar": forms.HiddenInput(),
        }

    def clean_first_name(self):
        val = (self.cleaned_data.get("first_name") or "").strip()
        if not val:
            raise forms.ValidationError("Ingresá tu nombre.")
        return val

    def clean_last_name(self):
        val = (self.cleaned_data.get("last_name") or "").strip()
        if not val:
            raise forms.ValidationError("Ingresá tu apellido.")
        return val
