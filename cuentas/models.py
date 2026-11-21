from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models.functions import Lower


class AdministradorUsuarios(UserManager):
    def _create_user(self, username, email, password, **extra_fields):
        return super()._create_user(
            username.strip().lower(),
            (email or "").strip().lower(),
            password,
            **extra_fields
        )

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.update(is_active=True, estado="aprobado")
        return super().create_superuser(username, email, password, **extra_fields)


class Usuario(AbstractUser):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        APROBADO = "aprobado", "Aprobado"
        RECHAZADO = "rechazado", "Rechazado"

    AVATAR_CHOICES = [
        ("neutral", "Neutral"),
        ("hombre", "Hombre"),
        ("mujer", "Mujer"),
    ]

    ROL_CHOICES = [
        ("socio_gerente", "Socio Gerente"),
        ("acopiador", "Acopiador (Centro Cachi)"),
        ("administracion", "Administración (Oficina Salta)"),
    ]

    email = models.EmailField("correo electrónico", unique=True)
    is_active = models.BooleanField("puede ingresar", default=False)
    estado = models.CharField(
        max_length=12, choices=Estado.choices, default=Estado.PENDIENTE
    )
    avatar = models.CharField(
        "avatar", max_length=20, choices=AVATAR_CHOICES, default="neutral"
    )
    rol = models.CharField(
        "rol en la empresa", max_length=25, choices=ROL_CHOICES, default="acopiador"
    )
    objects = AdministradorUsuarios()

    @property
    def avatar_img(self):
        return f"img/avatares/{self.avatar or 'neutral'}.png"

    @property
    def rol_display(self):
        if self.is_superuser:
            return "Socio Gerente"
        for code, label in self.ROL_CHOICES:
            if self.rol == code:
                return label
        return "Acopiador"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("email"), name="usuario_email_sin_mayusculas"
            ),
            models.UniqueConstraint(
                Lower("username"), name="usuario_nombre_sin_mayusculas"
            ),
            models.CheckConstraint(
                condition=models.Q(is_active=False) | models.Q(estado="aprobado"),
                name="activo_solo_aprobado",
            ),
        ]
