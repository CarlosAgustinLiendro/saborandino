from datetime import timedelta
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class Productor(models.Model):
    nombre_completo = models.CharField("nombre y apellido / razón social", max_length=120)
    cuit = models.CharField("CUIT", max_length=20, blank=True)
    localidad = models.CharField("localidad / zona", max_length=80, default="Cachi, Salta")
    telefono = models.CharField("teléfono", max_length=40, blank=True)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        ordering = ["nombre_completo"]
        verbose_name = "productor"
        verbose_name_plural = "productores"

    def __str__(self):
        return f"{self.nombre_completo} ({self.localidad})"


class Campania(models.Model):
    nombre = models.CharField("nombre de campaña", max_length=50, unique=True)
    fecha_inicio = models.DateField("fecha de inicio")
    fecha_fin = models.DateField("fecha de fin")
    activa = models.BooleanField("activa", default=True)

    class Meta:
        ordering = ["-fecha_inicio"]
        verbose_name = "campaña"
        verbose_name_plural = "campañas"

    def __str__(self):
        return self.nombre


class TipoMateriaPrima(models.Model):
    nombre = models.CharField("materia prima", max_length=80, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "tipo de materia prima"
        verbose_name_plural = "tipos de materia prima"

    def __str__(self):
        return self.nombre


class PrecioReferencia(models.Model):
    tipo_producto = models.ForeignKey(
        TipoMateriaPrima, on_delete=models.PROTECT, verbose_name="tipo de materia prima"
    )
    campania = models.ForeignKey(
        Campania, on_delete=models.PROTECT, verbose_name="campaña"
    )
    precio_por_kg = models.DecimalField(
        "precio por kg ($)",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    fecha_fijacion = models.DateTimeField("fecha de fijación", auto_now=True)
    fijado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="fijado por (Socio Gerente)",
    )

    class Meta:
        ordering = ["-fecha_fijacion"]
        unique_together = [("tipo_producto", "campania")]
        verbose_name = "precio de referencia"
        verbose_name_plural = "precios de referencia"

    def __str__(self):
        return f"{self.tipo_producto} - {self.campania}: ${self.precio_por_kg}/kg"


class ComprobanteAcopio(models.Model):
    numero = models.CharField("número de comprobante", max_length=30, unique=True)
    productor = models.ForeignKey(
        Productor, on_delete=models.PROTECT, verbose_name="productor"
    )
    tipo_producto = models.ForeignKey(
        TipoMateriaPrima, on_delete=models.PROTECT, verbose_name="materia prima"
    )
    campania = models.ForeignKey(
        Campania, on_delete=models.PROTECT, verbose_name="campaña"
    )
    fecha = models.DateField("fecha de recepción", default=timezone.now)
    procedencia = models.CharField("procedencia", max_length=100, default="Cachi, Salta")
    kilos_brutos = models.DecimalField(
        "kilos brutos",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    tara = models.DecimalField(
        "tara (kg)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    kilos_netos = models.DecimalField(
        "kilos netos",
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0.01)],
    )
    porcentaje_humedad = models.DecimalField(
        "porcentaje de humedad (%)",
        max_digits=5,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    precio_referencia = models.DecimalField(
        "precio de referencia aplicado ($/kg)",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    usuario_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="acopiador responsable",
    )
    observaciones = models.TextField("observaciones", blank=True)
    rectificado = models.BooleanField("rectificado", default=False)
    motivo_rectificacion = models.TextField("motivo de rectificación", blank=True)
    origen_offline = models.BooleanField("registrado en contingencia offline", default=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name = "comprobante de acopio"
        verbose_name_plural = "comprobantes de acopio"

    def __str__(self):
        return f"{self.numero} - {self.productor.nombre_completo} ({self.kilos_netos} kg)"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.kilos_brutos is not None and self.tara is not None:
            if self.kilos_brutos <= self.tara:
                raise ValidationError("Los kilos brutos deben ser mayores que la tara.")
            self.kilos_netos = self.kilos_brutos - self.tara

    def save(self, *args, **kwargs):
        if self.kilos_brutos is not None and self.tara is not None:
            self.kilos_netos = self.kilos_brutos - self.tara
        super().save(*args, **kwargs)


class Anticipo(models.Model):
    numero = models.CharField("número de anticipo", max_length=30, unique=True)
    productor = models.ForeignKey(
        Productor, on_delete=models.PROTECT, verbose_name="productor"
    )
    fecha = models.DateField("fecha de entrega", default=timezone.now)
    importe = models.DecimalField(
        "importe en efectivo ($)",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="anticipos_registrados",
        verbose_name="usuario que registró",
    )
    autorizado_por = models.CharField(
        "autorizado por", max_length=100, default="Roberto Zerpa (Socio Gerente)"
    )
    imputado = models.BooleanField("imputado en liquidación", default=False)
    observaciones = models.TextField("observaciones", blank=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name = "anticipo"
        verbose_name_plural = "anticipos"

    def __str__(self):
        return f"{self.numero} - {self.productor.nombre_completo} (${self.importe})"


class Liquidacion(models.Model):
    numero = models.CharField("número de liquidación", max_length=30, unique=True)
    comprobante = models.OneToOneField(
        ComprobanteAcopio,
        on_delete=models.PROTECT,
        related_name="liquidacion",
        verbose_name="comprobante de acopio",
    )
    fecha_liquidacion = models.DateField("fecha de liquidación", default=timezone.now)
    fecha_vencimiento = models.DateField("fecha de vencimiento (30 días corridos)")
    importe_bruto = models.DecimalField("importe bruto ($)", max_digits=12, decimal_places=2)
    total_anticipos = models.DecimalField("anticipos descontados ($)", max_digits=12, decimal_places=2, default=0)
    saldo_neto = models.DecimalField("saldo neto a pagar ($)", max_digits=12, decimal_places=2)
    usuario_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="responsable de liquidación",
    )
    estado = models.CharField(
        "estado",
        max_length=20,
        choices=[("Pendiente", "Pendiente"), ("Liquidado", "Liquidado")],
        default="Liquidado",
    )
    anticipos_aplicados = models.ManyToManyField(Anticipo, blank=True, verbose_name="anticipos imputados")

    class Meta:
        ordering = ["-fecha_liquidacion", "-id"]
        verbose_name = "liquidación a productor"
        verbose_name_plural = "liquidaciones a productores"

    def __str__(self):
        return f"{self.numero} - {self.comprobante.productor.nombre_completo} (${self.saldo_neto})"


class HistorialActividad(models.Model):
    ACCIONES = [
        ("RECEPCION_CREAR", "Creación de recepción de acopio"),
        ("RECEPCION_RECTIFICAR", "Rectificación de comprobante de acopio"),
        ("PRECIO_MODIFICAR", "Modificación de precio de referencia"),
        ("ANTICIPO_REGISTRAR", "Registro de anticipo en efectivo"),
        ("LIQUIDACION_EMITIR", "Emisión de liquidación"),
        ("PRODUCTOR_ACTUALIZAR", "Actualización de datos de productor"),
    ]
    fecha_hora = models.DateTimeField("fecha y hora", auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="usuario",
    )
    accion = models.CharField("acción", max_length=40, choices=ACCIONES)
    modulo = models.CharField("módulo", max_length=50)
    descripcion = models.TextField("descripción")
    comprobante_relacionado = models.CharField("comprobante / ref", max_length=50, blank=True)

    class Meta:
        ordering = ["-fecha_hora"]
        verbose_name = "registro de actividad"
        verbose_name_plural = "historial de actividades"

    def __str__(self):
        return f"[{self.fecha_hora.strftime('%d/%m/%Y %H:%M')}] {self.usuario}: {self.accion}"


def registrar_historial(usuario, accion, modulo, descripcion, comprobante_relacionado=""):
    try:
        return HistorialActividad.objects.create(
            usuario=usuario if (usuario and usuario.is_authenticated) else None,
            accion=accion,
            modulo=modulo,
            descripcion=descripcion,
            comprobante_relacionado=comprobante_relacionado,
        )
    except Exception:
        return None


