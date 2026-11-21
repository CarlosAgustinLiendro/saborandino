from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from catalogo.models import Categoria, Producto


class Command(BaseCommand):
    help = (
        "Agrega ejemplos reales de Sabor Andino S.R.L. sin modificar registros existentes. No crea cuentas."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--usuario", required=True, help="Nombre del administrador existente"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            usuario = get_user_model().objects.get(
                username=options["usuario"], is_superuser=True, is_active=True
            )
        except get_user_model().DoesNotExist:
            raise CommandError("Primero creá un administrador con createsuperuser.")

        productos_demo = [
            ("DEMO-001", "Ají Molido Picante", "Condimentos", "150 g", 28, "Valles Calchaquíes (Salta)", "12/26", "2850.00", "aji_molido.png"),
            ("DEMO-002", "Comino Molido", "Especias", "100 g", 45, "Cachi (Salta)", "10/26", "2400.00", "comino_molido.png"),
            ("DEMO-003", "Condimento Ricky Ricón", "Condimentos", "25 g", 40, "Salta Capital", "08/27", "1900.00", "aji_molido.png"),
            ("DEMO-004", "Curcuma Molida", "Especias", "50 g", 20, "Valles Calchaquíes", "11/26", "2100.00", "comino_molido.png"),
            ("DEMO-005", "Orégano en Hojas", "Aromáticas", "100 g", 35, "Molinos (Salta)", "01/27", "2200.00", "oregano_hojas.png"),
            ("DEMO-006", "Pimienta Negra en Grano", "Especias", "100 g", 50, "Cafayate (Salta)", "05/27", "3100.00", "pimienta_negra.png"),
        ]

        for codigo, nombre, categoria, presentacion, stock, origen, vencimiento, precio, imagen in productos_demo:
            cat = Categoria.objects.filter(nombre__iexact=categoria).first()
            if not cat:
                cat = Categoria.objects.create(nombre=categoria)
            if not Producto.objects.filter(codigo__iexact=codigo).exists():
                Producto.objects.create(
                    codigo=codigo,
                    nombre=nombre,
                    categoria=cat,
                    presentacion=presentacion,
                    stock=stock,
                    origen=origen,
                    vencimiento=vencimiento,
                    precio=precio,
                    imagen=imagen,
                    descripcion=f"{nombre} de producción artesanal en {origen}. Envasado en origen con trazabilidad garantizada.",
                    creado_por=usuario,
                    actualizado_por=usuario,
                )
        self.stdout.write(
            self.style.SUCCESS(
                "Ejemplos disponibles; los registros existentes se conservaron."
            )
        )
