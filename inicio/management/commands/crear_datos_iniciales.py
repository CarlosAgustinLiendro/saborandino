from datetime import date, timedelta
from decimal import Decimal
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from catalogo.models import Categoria, Producto
from acopio.models import (
    Productor,
    Campania,
    TipoMateriaPrima,
    PrecioReferencia,
    ComprobanteAcopio,
    Anticipo,
    Liquidacion,
)


class Command(BaseCommand):
    help = "Crea los usuarios iniciales, carga el catálogo y los datos de Acopio (productores, campañas, precios, recepciones y liquidaciones)."

    def handle(self, *args, **options):
        User = get_user_model()
        admin_user, created = User.objects.get_or_create(
            username="carlos",
            defaults={
                "email": "liendrocarlosagustin@gmail.com",
                "first_name": "Carlos Agustín",
                "last_name": "Liendro",
                "avatar": "hombre",
                "is_superuser": True,
                "is_staff": True,
                "is_active": True,
                "estado": "aprobado",
            },
        )
        if created:
            admin_user.set_password("SaborAndino2026!")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Administrador 'carlos' creado con éxito."))
        else:
            self.stdout.write("El usuario 'carlos' ya existe.")

        operador_user, op_created = User.objects.get_or_create(
            username="operador",
            defaults={
                "email": "operador@saborandino.com",
                "first_name": "María",
                "last_name": "González",
                "avatar": "mujer",
                "is_superuser": False,
                "is_staff": False,
                "is_active": True,
                "estado": "aprobado",
            },
        )
        if op_created:
            operador_user.set_password("SaborAndino2026!")
            operador_user.save()
            self.stdout.write(self.style.SUCCESS("Operador 'operador' creado con éxito."))

        call_command("cargar_demo", usuario="carlos")

        # ======================================================================
        # POBREZA / SEMILLERO DE ACOPIO Y LIQUIDACIÓN (GRUPO 7 - P2 Y P4)
        # ======================================================================
        # 1. Campañas
        campania_2026, _ = Campania.objects.get_or_create(
            nombre="Campaña Pimiento y Especias 2026",
            defaults={"fecha_inicio": date(2026, 1, 15), "fecha_fin": date(2026, 6, 30), "activa": True},
        )
        campania_2025, _ = Campania.objects.get_or_create(
            nombre="Campaña Cosecha 2025",
            defaults={"fecha_inicio": date(2025, 1, 10), "fecha_fin": date(2025, 6, 25), "activa": False},
        )

        # 2. Tipos de Materia Prima
        materias = [
            "Pimiento para pimentón",
            "Comino criollo",
            "Orégano de altura",
            "Anís estrellado y dulce",
            "Ají seco calchaquí",
            "Páprika dulce",
        ]
        materia_objs = {}
        for m in materias:
            obj, _ = TipoMateriaPrima.objects.get_or_create(nombre=m)
            materia_objs[m] = obj

        # 3. Precios de Referencia (HU-03 fijados por Socio Gerente)
        precios_config = [
            ("Pimiento para pimentón", Decimal("2850.00")),
            ("Comino criollo", Decimal("4200.00")),
            ("Orégano de altura", Decimal("3600.00")),
            ("Anís estrellado y dulce", Decimal("4800.00")),
            ("Ají seco calchaquí", Decimal("3100.00")),
            ("Páprika dulce", Decimal("3300.00")),
        ]
        for m_nombre, precio in precios_config:
            PrecioReferencia.objects.get_or_create(
                tipo_producto=materia_objs[m_nombre],
                campania=campania_2026,
                defaults={"precio_por_kg": precio, "fijado_por": admin_user},
            )

        # 4. Padrón de 47 Productores de los Valles Calchaquíes
        productores_nombres = [
            ("Finca Las Pailas (Familia Alancay)", "20-14285940-3", "Cachi, Salta", "+54 9 3868 49-1020"),
            ("Cooperativa Agropecuaria Calchaquí", "30-71124589-4", "San Carlos, Salta", "+54 9 3868 49-2045"),
            ("Productores Unidos de Molinos", "30-68954120-7", "Molinos, Salta", "+54 9 3868 49-3011"),
            ("Agropecuaria Cafayateña S.A.", "30-58963214-9", "Cafayate, Salta", "+54 9 3868 42-1540"),
            ("Finca La Poma Alta (Marcos Choque)", "20-22458710-5", "La Poma, Salta", "+54 9 3868 49-4088"),
            ("Asociación de Pequeños Productores Seclantás", "30-70894561-2", "Seclantás, Salta", "+54 9 3868 49-8012"),
            ("Establecimiento El Chañar (Héctor Guitián)", "20-18965412-3", "Cachi Adentro, Salta", "+54 9 3868 49-1155"),
            ("Agro San José (Faustino Mamaní)", "20-25632147-8", "San José de Cachi, Salta", "+54 9 3868 49-1240"),
            ("Finca Buena Vista (Valeriano Flores)", "20-16524890-4", "Payogasta, Salta", "+54 9 3868 49-5020"),
            ("Cooperativa Cachi Adentro Ltda.", "30-65478912-3", "Cachi, Salta", "+54 9 3868 49-1300"),
            ("Don Evaristo Colque", "20-13654789-2", "Molinos, Salta", "+54 9 3868 49-3050"),
            ("Finca El Colomé (Aromáticas)", "30-54123698-7", "Colomé, Salta", "+54 9 3868 49-3120"),
            ("Hermanos Tolaba (Finca Potrero)", "20-28745120-6", "Potrero de Payogasta, Salta", "+54 9 3868 49-5110"),
            ("Agropecuaria Santa Rosa (Fabián Burgos)", "20-21458963-1", "San Carlos, Salta", "+54 9 3868 49-2180"),
            ("Finca Las Flechas (Esteban Liendro)", "20-17854123-9", "Angastaco, Salta", "+54 9 3868 49-6010"),
            ("Productores Orgánicos de Seclantás", "30-71452369-8", "Seclantás, Salta", "+54 9 3868 49-8050"),
            ("Comunidad Originaria Cachi", "30-69852147-1", "Cachi, Salta", "+54 9 3868 49-1420"),
            ("Finca El Algarrobal (Néstor Cruz)", "20-24158963-5", "Cafayate, Salta", "+54 9 3868 42-1890"),
            ("Agropecuaria El Barreal (Raúl Ramos)", "20-19852147-4", "San Carlos, Salta", "+54 9 3868 49-2230"),
            ("Finca Las Tipas (Domingo Chaile)", "20-23654128-0", "Cachi, Salta", "+54 9 3868 49-1510"),
            ("Establecimiento San Antonio", "30-63258741-9", "Animaná, Salta", "+54 9 3868 42-2010"),
            ("Agrícola Los Sauces (Lucio Quispe)", "20-26985412-3", "Payogasta, Salta", "+54 9 3868 49-5240"),
            ("Finca Los Molles (Severo Calpanchay)", "20-15896324-7", "Molinos, Salta", "+54 9 3868 49-3220"),
            ("Emprendimiento El Churqui", "30-72154896-3", "Cachi, Salta", "+54 9 3868 49-1600"),
            ("Finca Valle Hermoso (Simón Condorí)", "20-20147852-6", "Seclantás, Salta", "+54 9 3868 49-8110"),
            ("Agro San Bernardo (Tomás Vilca)", "20-27412589-5", "La Poma, Salta", "+54 9 3868 49-4150"),
            ("Productores Asociados de Tolombón", "30-67895412-4", "Tolombón, Salta", "+54 9 3868 42-3020"),
            ("Finca Las Arcas (Felipe Morales)", "20-18452178-9", "San Carlos, Salta", "+54 9 3868 49-2310"),
            ("Establecimiento Cachi Viejo", "30-70145896-1", "Cachi, Salta", "+54 9 3868 49-1720"),
            ("Finca La Falda (Bernardino Yapura)", "20-22145896-3", "Angastaco, Salta", "+54 9 3868 49-6120"),
            ("Cooperativa Aromas del Valle", "30-71895241-0", "Molinos, Salta", "+54 9 3868 49-3340"),
            ("Finca El Cardón (Vicente Viveros)", "20-16985214-8", "Payogasta, Salta", "+54 9 3868 49-5310"),
            ("Agropecuaria Las Pircas", "30-64589632-8", "Cafayate, Salta", "+54 9 3868 42-2550"),
            ("Finca Monte Carmelo (Celso Casimiro)", "20-25412896-4", "Seclantás, Salta", "+54 9 3868 49-8230"),
            ("Establecimiento San Rafael", "30-68412596-7", "Cachi, Salta", "+54 9 3868 49-1830"),
            ("Finca La Aguada (Eusebio Lamas)", "20-21896541-2", "La Poma, Salta", "+54 9 3868 49-4220"),
            ("Agropecuaria Calchaquí Norte", "30-72654128-5", "San Carlos, Salta", "+54 9 3868 49-2450"),
            ("Finca La Candelaria (Mario Guaymás)", "20-19458712-0", "Molinos, Salta", "+54 9 3868 49-3460"),
            ("Emprendimiento Especias del Sol", "30-70589632-4", "Animaná, Salta", "+54 9 3868 42-2680"),
            ("Finca Bella Vista (Justo Zerpa)", "20-23412589-7", "Cachi, Salta", "+54 9 3868 49-1910"),
            ("Agro El Rodeo (Santos Corregidor)", "20-26145896-1", "Payogasta, Salta", "+54 9 3868 49-5420"),
            ("Finca Las Rosas (Damiano Mamaní)", "20-17452189-6", "Angastaco, Salta", "+54 9 3868 49-6230"),
            ("Establecimiento Los Pinos", "30-69124587-3", "Cafayate, Salta", "+54 9 3868 42-2890"),
            ("Finca La Puerta (Bonifacio Choque)", "20-24895632-5", "Seclantás, Salta", "+54 9 3868 49-8350"),
            ("Agropecuaria Los Sauces del Valle", "30-71325896-9", "Molinos, Salta", "+54 9 3868 49-3580"),
            ("Finca El Trébol (Crisanto Alancay)", "20-20895412-8", "Cachi, Salta", "+54 9 3868 49-1990"),
            ("Sociedad Agrícola Calchaquí", "30-65894123-6", "San Carlos, Salta", "+54 9 3868 49-2590"),
        ]

        for nombre, cuit, loc, tel in productores_nombres:
            Productor.objects.get_or_create(
                nombre_completo=nombre,
                defaults={"cuit": cuit, "localidad": loc, "telefono": tel, "activo": True},
            )

        # 5. Generar Recepciones, Anticipos y Liquidaciones de demostración
        p1 = Productor.objects.get(nombre_completo="Finca Las Pailas (Familia Alancay)")
        p2 = Productor.objects.get(nombre_completo="Cooperativa Agropecuaria Calchaquí")
        p3 = Productor.objects.get(nombre_completo="Productores Unidos de Molinos")

        # Anticipo previo para Finca Las Pailas (HU-04)
        ant1, _ = Anticipo.objects.get_or_create(
            numero="ANT-2026-001",
            defaults={
                "productor": p1,
                "fecha": date(2026, 2, 10),
                "importe": Decimal("350000.00"),
                "usuario_registro": admin_user,
                "autorizado_por": "Roberto Zerpa (Socio Gerente)",
                "imputado": True,
                "observaciones": "Anticipo de flete y jornal de cosecha.",
            },
        )

        # Anticipo pendiente para Cooperativa Calchaquí
        Anticipo.objects.get_or_create(
            numero="ANT-2026-002",
            defaults={
                "productor": p2,
                "fecha": date(2026, 2, 20),
                "importe": Decimal("500000.00"),
                "usuario_registro": admin_user,
                "autorizado_por": "Roberto Zerpa (Socio Gerente)",
                "imputado": False,
                "observaciones": "Adelanto en efectivo para acopio de comino criollo.",
            },
        )

        # Recepción 1 para Finca Las Pailas (HU-01, HU-02)
        rec1, r1_created = ComprobanteAcopio.objects.get_or_create(
            numero="REC-2026-001",
            defaults={
                "productor": p1,
                "tipo_producto": materia_objs["Pimiento para pimentón"],
                "campania": campania_2026,
                "fecha": date(2026, 2, 18),
                "procedencia": "Cachi, Salta",
                "kilos_brutos": Decimal("3450.00"),
                "tara": Decimal("1200.00"),
                "kilos_netos": Decimal("2250.00"),
                "porcentaje_humedad": Decimal("12.50"),
                "precio_referencia": Decimal("2850.00"),
                "usuario_responsable": operador_user,
                "observaciones": "Cargamento en bolsas de arpillera en óptimas condiciones.",
            },
        )

        # Liquidación 1 con imputación de anticipo y 30 días de vencimiento (HU-05)
        if not hasattr(rec1, "liquidacion"):
            bruto1 = rec1.kilos_netos * rec1.precio_referencia
            saldo1 = bruto1 - ant1.importe
            venc1 = rec1.fecha + timedelta(days=30)
            liq1 = Liquidacion.objects.create(
                numero="LIQ-2026-001",
                comprobante=rec1,
                fecha_liquidacion=date(2026, 2, 19),
                fecha_vencimiento=venc1,
                importe_bruto=bruto1,
                total_anticipos=ant1.importe,
                saldo_neto=saldo1,
                usuario_responsable=admin_user,
                estado="Liquidado",
            )
            liq1.anticipos_aplicados.add(ant1)

        # Recepción 2 para Cooperativa Calchaquí
        ComprobanteAcopio.objects.get_or_create(
            numero="REC-2026-002",
            defaults={
                "productor": p2,
                "tipo_producto": materia_objs["Comino criollo"],
                "campania": campania_2026,
                "fecha": date(2026, 2, 25),
                "procedencia": "San Carlos, Salta",
                "kilos_brutos": Decimal("2100.00"),
                "tara": Decimal("950.00"),
                "kilos_netos": Decimal("1150.00"),
                "porcentaje_humedad": Decimal("10.80"),
                "precio_referencia": Decimal("4200.00"),
                "usuario_responsable": operador_user,
                "observaciones": "Comino criollo seleccionado primera calidad.",
            },
        )

        # Recepción 3 para Productores Unidos de Molinos
        ComprobanteAcopio.objects.get_or_create(
            numero="REC-2026-003",
            defaults={
                "productor": p3,
                "tipo_producto": materia_objs["Orégano de altura"],
                "campania": campania_2026,
                "fecha": date(2026, 3, 2),
                "procedencia": "Molinos, Salta",
                "kilos_brutos": Decimal("1800.00"),
                "tara": Decimal("850.00"),
                "kilos_netos": Decimal("950.00"),
                "porcentaje_humedad": Decimal("9.50"),
                "precio_referencia": Decimal("3600.00"),
                "usuario_responsable": operador_user,
                "observaciones": "Orégano en hoja seca despalillada.",
            },
        )

        self.stdout.write(self.style.SUCCESS("47 Productores, Campañas, Precios, Recepciones y Liquidaciones cargados correctamente."))
