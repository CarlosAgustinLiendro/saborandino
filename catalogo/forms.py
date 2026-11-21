from django import forms
from .models import Categoria, Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = (
            "codigo",
            "nombre",
            "categoria",
            "presentacion",
            "stock",
            "origen",
            "vencimiento",
            "precio",
            "descripcion",
            "archivo_imagen",
        )
        widgets = {
            "codigo": forms.TextInput(attrs={"placeholder": "Ej. ESP-001", "class": "input-redondeado"}),
            "nombre": forms.TextInput(attrs={"placeholder": "Ej. Ají Molido Picante, Comino Molido...", "class": "input-redondeado"}),
            "categoria": forms.Select(attrs={"class": "input-redondeado", "style": "border-radius:24px;"}),
            "presentacion": forms.TextInput(attrs={"placeholder": "Ej. 150 g, 100 g, 1 kg", "class": "input-redondeado"}),
            "origen": forms.TextInput(attrs={"placeholder": "Ej. Valles Calchaquíes (Salta)", "class": "input-redondeado"}),
            "vencimiento": forms.TextInput(attrs={"placeholder": "Ej. 12/26", "class": "input-redondeado"}),
            "stock": forms.NumberInput(attrs={"placeholder": "0", "min": "0", "class": "input-redondeado"}),
            "precio": forms.NumberInput(attrs={"placeholder": "0.00", "step": "0.01", "min": "0", "class": "input-redondeado"}),
            "descripcion": forms.Textarea(attrs={"rows": 3, "placeholder": "Información adicional del producto, características y notas de conservación...", "class": "input-redondeado", "style": "border-radius:18px;"}),
            "archivo_imagen": forms.FileInput(attrs={"accept": "image/*", "id": "input-archivo-imagen", "style": "display:none;"}),
        }

    def clean_codigo(self):
        codigo = (self.cleaned_data.get("codigo") or "").strip().upper()
        if not codigo:
            import random
            codigo = f"SA-{random.randint(100, 999)}"
        if (
            Producto.objects.filter(codigo__iexact=codigo)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("Ya existe un producto con ese código.")
        return codigo


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ("nombre",)

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        if (
            Categoria.objects.filter(nombre__iexact=nombre)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("Ya existe esa categoría.")
        return nombre
