from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse


class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "categoría"
        constraints = [
            models.UniqueConstraint(
                Lower("nombre"), name="categoria_nombre_sin_mayusculas"
            )
        ]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    codigo = models.CharField("código", max_length=30, unique=True)
    nombre = models.CharField(max_length=120)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, verbose_name="categoría"
    )
    presentacion = models.CharField(
        "presentación", max_length=50, blank=True, default="100 g"
    )
    origen = models.CharField(
        "origen", max_length=100, blank=True, default="Valles Calchaquíes (Salta)"
    )
    vencimiento = models.CharField(
        "vencimiento", max_length=30, blank=True, default="12/26"
    )
    descripcion = models.TextField("descripción", blank=True, max_length=2000)
    precio = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=0.00
    )
    stock = models.PositiveIntegerField(default=0)
    imagen = models.CharField(
        "imagen", max_length=100, blank=True, default="comino_molido.png"
    )
    archivo_imagen = models.FileField(
        "archivo de imagen desde PC",
        upload_to="productos/",
        blank=True,
        null=True,
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="productos_creados",
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="productos_actualizados",
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    @property
    def imagen_rel(self):
        if self.archivo_imagen and hasattr(self.archivo_imagen, "name") and self.archivo_imagen.name:
            return ""
        if self.imagen:
            return f"img/productos/{self.imagen}"
        nom = self.nombre.lower()
        if "aji" in nom or "ají" in nom or "piment" in nom:
            return "img/productos/aji_molido.png"
        elif "oregano" in nom or "orégano" in nom:
            return "img/productos/oregano_hojas.png"
        elif "pimienta" in nom:
            return "img/productos/pimienta_negra.png"
        return "img/productos/comino_molido.png"

    def get_imagen_url(self):
        if self.archivo_imagen and hasattr(self.archivo_imagen, "url"):
            try:
                return self.archivo_imagen.url
            except ValueError:
                pass
        return f"{settings.STATIC_URL}{self.imagen_rel}"

    class Meta:
        ordering = ["nombre", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(precio__gte=0), name="producto_precio_no_negativo"
            ),
            models.UniqueConstraint(
                Lower("codigo"), name="producto_codigo_sin_mayusculas"
            ),
        ]

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse("catalogo:detalle", args=[self.pk])
