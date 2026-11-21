from django import forms
from django.core.exceptions import ValidationError
from .models import ComprobanteAcopio, Anticipo, PrecioReferencia, Productor, Campania, TipoMateriaPrima


class ComprobanteAcopioForm(forms.ModelForm):
    class Meta:
        model = ComprobanteAcopio
        fields = [
            "productor",
            "tipo_producto",
            "campania",
            "fecha",
            "procedencia",
            "kilos_brutos",
            "tara",
            "porcentaje_humedad",
            "observaciones",
        ]
        widgets = {
            "productor": forms.Select(attrs={"class": "input-redondeado"}),
            "tipo_producto": forms.Select(attrs={"class": "input-redondeado"}),
            "campania": forms.Select(attrs={"class": "input-redondeado"}),
            "fecha": forms.DateInput(attrs={"type": "date", "class": "input-redondeado"}),
            "procedencia": forms.TextInput(attrs={"placeholder": "Ej. Cachi, Finca Las Pailas", "class": "input-redondeado"}),
            "kilos_brutos": forms.NumberInput(attrs={"placeholder": "0.00", "step": "0.01", "class": "input-redondeado", "id": "id_kilos_brutos"}),
            "tara": forms.NumberInput(attrs={"placeholder": "0.00", "step": "0.01", "class": "input-redondeado", "id": "id_tara"}),
            "porcentaje_humedad": forms.NumberInput(attrs={"placeholder": "Ej. 12.5", "step": "0.1", "min": "0", "max": "100", "class": "input-redondeado"}),
            "observaciones": forms.Textarea(attrs={"rows": 2, "placeholder": "Observaciones de la carga, estado de bolsas, etc.", "class": "input-redondeado"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "productor" in self.fields:
            self.fields["productor"].empty_label = "-- Seleccionar productor --"
        if "tipo_producto" in self.fields:
            self.fields["tipo_producto"].empty_label = "-- Seleccionar materia prima --"
        if "campania" in self.fields:
            self.fields["campania"].empty_label = "-- Seleccionar campaña --"

    def clean(self):
        cleaned_data = super().clean()
        kilos_brutos = cleaned_data.get("kilos_brutos")
        tara = cleaned_data.get("tara")
        humedad = cleaned_data.get("porcentaje_humedad")

        if kilos_brutos is not None and tara is not None:
            if kilos_brutos <= tara:
                raise ValidationError("Los kilos brutos deben ser mayores que la tara del camión/envase.")

        if humedad is not None and (humedad < 0 or humedad > 100):
            raise ValidationError("El porcentaje de humedad debe estar comprendido entre 0% y 100%.")

        return cleaned_data


class AnticipoForm(forms.ModelForm):
    class Meta:
        model = Anticipo
        fields = ["productor", "fecha", "importe", "autorizado_por", "observaciones"]
        widgets = {
            "productor": forms.Select(attrs={"class": "input-redondeado"}),
            "fecha": forms.DateInput(attrs={"type": "date", "class": "input-redondeado"}),
            "importe": forms.NumberInput(attrs={"placeholder": "Importe en pesos ($)", "step": "0.01", "min": "0.01", "class": "input-redondeado"}),
            "autorizado_por": forms.TextInput(attrs={"placeholder": "Ej. Roberto Zerpa (Socio Gerente)", "class": "input-redondeado"}),
            "observaciones": forms.Textarea(attrs={"rows": 2, "placeholder": "Motivo del anticipo en efectivo...", "class": "input-redondeado"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "productor" in self.fields:
            self.fields["productor"].empty_label = "-- Seleccionar productor --"

    def clean_importe(self):
        importe = self.cleaned_data.get("importe")
        if importe is None or importe <= 0:
            raise ValidationError("El importe del anticipo debe ser un valor positivo mayor a cero.")
        return importe


class PrecioReferenciaForm(forms.ModelForm):
    class Meta:
        model = PrecioReferencia
        fields = ["tipo_producto", "campania", "precio_por_kg"]
        widgets = {
            "tipo_producto": forms.Select(attrs={"class": "input-redondeado"}),
            "campania": forms.Select(attrs={"class": "input-redondeado"}),
            "precio_por_kg": forms.NumberInput(attrs={"placeholder": "Precio por kg ($)", "step": "0.01", "min": "0.01", "class": "input-redondeado"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "tipo_producto" in self.fields:
            self.fields["tipo_producto"].empty_label = "-- Seleccionar materia prima --"
        if "campania" in self.fields:
            self.fields["campania"].empty_label = "-- Seleccionar campaña --"


class ProductorForm(forms.ModelForm):
    class Meta:
        model = Productor
        fields = ["nombre_completo", "cuit", "localidad", "telefono", "activo"]
        widgets = {
            "nombre_completo": forms.TextInput(attrs={"placeholder": "Nombre completo o Razón Social", "class": "input-redondeado"}),
            "cuit": forms.TextInput(attrs={"placeholder": "XX-XXXXXXXX-X", "class": "input-redondeado"}),
            "localidad": forms.TextInput(attrs={"placeholder": "Ej. Cachi, Molinos, Seclantás", "class": "input-redondeado"}),
            "telefono": forms.TextInput(attrs={"placeholder": "Teléfono de contacto", "class": "input-redondeado"}),
            "activo": forms.CheckboxInput(attrs={"style": "width:auto; margin-top:6px;"}),
        }


class RectificacionForm(forms.ModelForm):
    motivo_rectificacion = forms.CharField(
        label="Motivo de la rectificación y autorización",
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "Detallar el motivo de la corrección y quién autorizó (ej. 'Pesaje corregido por tara de cajones errónea - Aut. Roberto Zerpa')...",
            "class": "input-redondeado",
            "required": True,
        }),
    )

    class Meta:
        model = ComprobanteAcopio
        fields = ["kilos_brutos", "tara", "porcentaje_humedad", "observaciones", "motivo_rectificacion"]
        widgets = {
            "kilos_brutos": forms.NumberInput(attrs={"step": "0.01", "class": "input-redondeado", "id": "id_kilos_brutos"}),
            "tara": forms.NumberInput(attrs={"step": "0.01", "class": "input-redondeado", "id": "id_tara"}),
            "porcentaje_humedad": forms.NumberInput(attrs={"step": "0.1", "min": "0", "max": "100", "class": "input-redondeado"}),
            "observaciones": forms.Textarea(attrs={"rows": 2, "class": "input-redondeado"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        kilos_brutos = cleaned_data.get("kilos_brutos")
        tara = cleaned_data.get("tara")
        humedad = cleaned_data.get("porcentaje_humedad")
        motivo = cleaned_data.get("motivo_rectificacion")

        if kilos_brutos is not None and tara is not None:
            if kilos_brutos <= tara:
                raise ValidationError("Los kilos brutos deben ser mayores que la tara.")

        if humedad is not None and (humedad < 0 or humedad > 100):
            raise ValidationError("El porcentaje de humedad debe estar entre 0% y 100%.")

        if not motivo or not motivo.strip():
            raise ValidationError("Debe ingresar obligatoriamente un motivo para la rectificación.")

        return cleaned_data

