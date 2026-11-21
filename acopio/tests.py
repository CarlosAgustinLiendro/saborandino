from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
from .models import (
    Productor,
    Campania,
    TipoMateriaPrima,
    PrecioReferencia,
    ComprobanteAcopio,
    Anticipo,
    Liquidacion,
    HistorialActividad,
)

User = get_user_model()


class AcopioHU1ToHU7Tests(TestCase):
    def setUp(self):
        self.gerente = User.objects.create_superuser(
            username="gerente_test",
            email="gerente@saborandino.com",
            password="GerentePassword2026!",
            first_name="Roberto",
            last_name="Zerpa",
        )
        self.acopiador = User.objects.create_user(
            username="acopiador_cachi",
            email="acopiador@saborandino.com",
            password="AcopiadorPassword2026!",
            first_name="María",
            last_name="González",
            is_active=True,
            estado="aprobado",
        )
        self.productor = Productor.objects.create(
            nombre_completo="Finca Las Pailas (Familia Alancay)",
            cuit="20-14285940-3",
            localidad="Cachi, Salta",
        )
        self.campania = Campania.objects.create(
            nombre="Campaña 2026 Test",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 6, 30),
        )
        self.tipo_producto = TipoMateriaPrima.objects.create(
            nombre="Pimiento para pimentón"
        )
        self.precio_ref = PrecioReferencia.objects.create(
            tipo_producto=self.tipo_producto,
            campania=self.campania,
            precio_por_kg=Decimal("2850.00"),
            fijado_por=self.gerente,
        )

    def test_hu01_calculo_kilos_netos_y_validacion_tara(self):
        """HU-01: Calcula kilos netos (bruto - tara) y valida que bruto > tara."""
        comprobante = ComprobanteAcopio(
            numero="REC-2026-TEST1",
            productor=self.productor,
            tipo_producto=self.tipo_producto,
            campania=self.campania,
            fecha=date(2026, 2, 20),
            kilos_brutos=Decimal("3500.00"),
            tara=Decimal("1200.00"),
            porcentaje_humedad=Decimal("12.0"),
            precio_referencia=Decimal("2850.00"),
            usuario_responsable=self.acopiador,
        )
        comprobante.full_clean()
        comprobante.save()
        self.assertEqual(comprobante.kilos_netos, Decimal("2300.00"))

        # Validar rechazo si bruto <= tara
        comprobante_invalido = ComprobanteAcopio(
            numero="REC-2026-TEST2",
            productor=self.productor,
            tipo_producto=self.tipo_producto,
            campania=self.campania,
            fecha=date(2026, 2, 20),
            kilos_brutos=Decimal("1000.00"),
            tara=Decimal("1200.00"),
            porcentaje_humedad=Decimal("12.0"),
            precio_referencia=Decimal("2850.00"),
            usuario_responsable=self.acopiador,
        )
        with self.assertRaises(ValidationError):
            comprobante_invalido.full_clean()

    def test_hu02_emision_comprobante_humedad_y_detalle(self):
        """HU-02: Humedad en rango 0-100%, vista de comprobante imprimible."""
        client = Client(SERVER_NAME="localhost")
        client.force_login(self.acopiador)

        resp = client.post(
            reverse("acopio:recepcion_crear"),
            {
                "productor": self.productor.id,
                "tipo_producto": self.tipo_producto.id,
                "campania": self.campania.id,
                "fecha": "2026-03-01",
                "procedencia": "Cachi Adentro",
                "kilos_brutos": "4000.00",
                "tara": "1500.00",
                "porcentaje_humedad": "11.5",
                "observaciones": "Lote impecable",
            },
        )
        # Redirige al detalle del nuevo comprobante
        self.assertEqual(resp.status_code, 302)
        comprobante = ComprobanteAcopio.objects.get(numero="REC-2026-001")
        self.assertEqual(comprobante.kilos_netos, Decimal("2500.00"))

        # Acceder a la vista de comprobante oficial
        resp_detalle = client.get(reverse("acopio:recepcion_detalle", args=[comprobante.id]))
        self.assertEqual(resp_detalle.status_code, 200)
        self.assertContains(resp_detalle, "COMPROBANTE DE ACOPIO")
        self.assertContains(resp_detalle, "REC-2026-001")
        self.assertContains(resp_detalle, "2500")

    def test_hu03_precios_referencia_restringido_a_socio_gerente(self):
        """HU-03: Solo el Socio Gerente (superuser) puede fijar o modificar precios."""
        client_acopiador = Client(SERVER_NAME="localhost")
        client_acopiador.force_login(self.acopiador)
        resp_denegado = client_acopiador.get(reverse("acopio:precio_crear"))
        # Operador común no tiene permiso
        self.assertEqual(resp_denegado.status_code, 403)

        client_gerente = Client(SERVER_NAME="localhost")
        client_gerente.force_login(self.gerente)
        resp_permitido = client_gerente.get(reverse("acopio:precio_crear"))
        self.assertEqual(resp_permitido.status_code, 200)

        # Gerente modifica el precio
        resp_mod = client_gerente.post(
            reverse("acopio:precio_editar", args=[self.precio_ref.id]),
            {
                "tipo_producto": self.tipo_producto.id,
                "campania": self.campania.id,
                "precio_por_kg": "3200.00",
            },
        )
        self.assertEqual(resp_mod.status_code, 302)
        self.precio_ref.refresh_from_db()
        self.assertEqual(self.precio_ref.precio_por_kg, Decimal("3200.00"))

    def test_hu04_registro_anticipo_y_validacion_importe(self):
        """HU-04: Registro de anticipo en efectivo con rechazo de importes <= 0."""
        client = Client(SERVER_NAME="localhost")
        client.force_login(self.gerente)

        # Rechazar importe <= 0
        resp_error = client.post(
            reverse("acopio:anticipo_crear"),
            {
                "productor": self.productor.id,
                "fecha": "2026-02-15",
                "importe": "-1000.00",
                "autorizado_por": "Roberto Zerpa",
            },
        )
        self.assertEqual(Anticipo.objects.count(), 0)

        # Aceptar importe positivo
        resp_ok = client.post(
            reverse("acopio:anticipo_crear"),
            {
                "productor": self.productor.id,
                "fecha": "2026-02-15",
                "importe": "150000.00",
                "autorizado_por": "Roberto Zerpa",
                "observaciones": "Anticipo de cosecha",
            },
        )
        self.assertEqual(resp_ok.status_code, 302)
        anticipo = Anticipo.objects.first()
        self.assertEqual(anticipo.importe, Decimal("150000.00"))
        self.assertFalse(anticipo.imputado)

    def test_hu05_liquidacion_saldo_vencimiento_30_dias_y_sin_duplicar(self):
        """
        HU-05: Liquidación calcula bruto, descuenta anticipos sin duplicar,
        establece vencimiento a 30 días corridos e incluye aclaración fiscal.
        """
        # Crear anticipo de $ 100.000
        anticipo = Anticipo.objects.create(
            numero="ANT-TEST-001",
            productor=self.productor,
            fecha=date(2026, 2, 1),
            importe=Decimal("100000.00"),
            usuario_registro=self.gerente,
            autorizado_por="Roberto Zerpa",
            imputado=False,
        )

        # Crear comprobante de 1000 kg a $ 2850 = $ 2.850.000 bruto
        comprobante = ComprobanteAcopio.objects.create(
            numero="REC-TEST-LIQ",
            productor=self.productor,
            tipo_producto=self.tipo_producto,
            campania=self.campania,
            fecha=date(2026, 2, 10),
            kilos_brutos=Decimal("2000.00"),
            tara=Decimal("1000.00"),
            kilos_netos=Decimal("1000.00"),
            porcentaje_humedad=Decimal("12.0"),
            precio_referencia=Decimal("2850.00"),
            usuario_responsable=self.acopiador,
        )

        client = Client(SERVER_NAME="localhost")
        client.force_login(self.gerente)

        # Generar liquidación
        resp_gen = client.get(reverse("acopio:liquidacion_generar", args=[comprobante.id]))
        self.assertEqual(resp_gen.status_code, 302)

        liquidacion = Liquidacion.objects.get(comprobante=comprobante)
        self.assertEqual(liquidacion.importe_bruto, Decimal("2850000.00"))
        self.assertEqual(liquidacion.total_anticipos, Decimal("100000.00"))
        self.assertEqual(liquidacion.saldo_neto, Decimal("2750000.00"))

        # Vencimiento debe ser exactamente 30 días corridos desde comprobante.fecha
        self.assertEqual(liquidacion.fecha_vencimiento, comprobante.fecha + timedelta(days=30))

        # Verificar que el anticipo quedó marcado como imputado
        anticipo.refresh_from_db()
        self.assertTrue(anticipo.imputado)

        # Verificar comprobante impreso con aclaración fiscal
        resp_det = client.get(reverse("acopio:liquidacion_detalle", args=[liquidacion.id]))
        self.assertEqual(resp_det.status_code, 200)
        self.assertContains(resp_det, "El presente comprobante interno de liquidación no reemplaza una factura fiscal.")

    def test_reestablecer_password_flujo_seguro_correo(self):
        """Prueba que el reseteo de contraseña requiere confirmación vía enlace seguro por correo."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        client = Client(SERVER_NAME="localhost")
        # 1. Pantalla de solicitud de enlace por correo
        resp_get = client.get(reverse("cuentas:reestablecer"))
        self.assertEqual(resp_get.status_code, 200)
        self.assertContains(resp_get, "Enviar enlace a mi correo")

        # 2. Solicitar enlace para el correo del usuario
        resp_post = client.post(
            reverse("cuentas:reestablecer"),
            {"email": "acopiador@saborandino.com"},
        )
        self.assertEqual(resp_post.status_code, 302)
        self.assertTrue(resp_post.url.startswith(reverse("cuentas:reestablecer_enviado")))

        resp_enviado = client.get(resp_post.url)
        self.assertEqual(resp_enviado.status_code, 200)
        self.assertContains(resp_enviado, "¡Revisá tu correo!")

        # 3. Acceder al enlace con token criptográfico
        token = default_token_generator.make_token(self.acopiador)
        uidb64 = urlsafe_base64_encode(force_bytes(self.acopiador.pk))
        confirmar_url = reverse(
            "cuentas:reestablecer_confirmar",
            kwargs={"uidb64": uidb64, "token": token},
        )

        resp_conf = client.get(confirmar_url)
        self.assertEqual(resp_conf.status_code, 200)
        self.assertContains(resp_conf, "Definir nueva contraseña")

        # 4. Establecer la nueva contraseña
        nueva_clave = "NuevaClaveSegura2026!"
        resp_cambio = client.post(
            confirmar_url,
            {"password1": nueva_clave, "password2": nueva_clave},
        )
        self.assertEqual(resp_cambio.status_code, 302)
        self.assertRedirects(resp_cambio, reverse("cuentas:login"))

        # 5. Iniciar sesión con la nueva clave restablecida vía login
        resp_login = client.post(
            reverse("cuentas:login"),
            {"username": "acopiador_cachi", "password": nueva_clave},
        )
        self.assertEqual(resp_login.status_code, 302)
        self.assertRedirects(resp_login, reverse("inicio:home"))

    # ==========================================================================
    # CASOS DE PRUEBA DE LA MATRIZ DE ACEPTACIÓN DEL INFORME (PÁGINA 15)
    # ==========================================================================

    def test_matriz_01_crear_comprobante_completo_y_rechazar_vacios(self):
        """Matriz P1: Crear comprobante con datos completos; rechazar campos obligatorios vacíos."""
        client = Client(SERVER_NAME="localhost")
        client.force_login(self.acopiador)

        # 1. Intento con campos vacíos
        resp_vacio = client.post(reverse("acopio:recepcion_crear"), {})
        self.assertEqual(resp_vacio.status_code, 200)
        self.assertTrue(resp_vacio.context["form"].errors)

        # 2. Envío con datos completos y válidos
        resp_ok = client.post(
            reverse("acopio:recepcion_crear"),
            {
                "productor": self.productor.id,
                "tipo_producto": self.tipo_producto.id,
                "campania": self.campania.id,
                "fecha": "2026-03-10",
                "procedencia": "Finca Las Pailas, Cachi",
                "kilos_brutos": "5200.00",
                "tara": "1200.00",
                "porcentaje_humedad": "10.5",
                "observaciones": "Entrega de prueba",
            },
        )
        self.assertEqual(resp_ok.status_code, 302)
        nuevo_comp = ComprobanteAcopio.objects.get(kilos_brutos=Decimal("5200.00"))
        self.assertEqual(nuevo_comp.kilos_netos, Decimal("4000.00"))

    def test_matriz_02_simular_18_entradas_jornada_y_recuperar_por_filtros(self):
        """Matriz P1: Registrar 18 entradas de prueba en una jornada simulada y recuperarlas por filtros."""
        fecha_simulada = date(2026, 3, 15)
        for i in range(1, 19):
            ComprobanteAcopio.objects.create(
                numero=f"REC-2026-SIM-{i:03d}",
                productor=self.productor,
                tipo_producto=self.tipo_producto,
                campania=self.campania,
                fecha=fecha_simulada,
                kilos_brutos=Decimal("3000.00") + Decimal(i * 10),
                tara=Decimal("1000.00"),
                porcentaje_humedad=Decimal("11.0"),
                precio_referencia=Decimal("2850.00"),
                usuario_responsable=self.acopiador,
            )

        client = Client(SERVER_NAME="localhost")
        client.force_login(self.acopiador)

        # Recuperar por filtro de fecha de la jornada
        resp = client.get(reverse("acopio:recepciones_lista"), {"fecha": "2026-03-15"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["comprobantes"].count(), 18)

    def test_matriz_03_bruto_100_tara_2_netos_98_y_casos_borde(self):
        """Matriz P1: Probar bruto 100 kg / tara 2 kg -> 98 kg netos; casos borde bruto <= tara -> ValidationError."""
        # 1. Caso base 100 kg / 2 kg = 98 kg
        comp_98 = ComprobanteAcopio(
            numero="REC-2026-98KG",
            productor=self.productor,
            tipo_producto=self.tipo_producto,
            campania=self.campania,
            fecha=date(2026, 3, 20),
            kilos_brutos=Decimal("100.00"),
            tara=Decimal("2.00"),
            porcentaje_humedad=Decimal("10.0"),
            precio_referencia=Decimal("2850.00"),
            usuario_responsable=self.acopiador,
        )
        comp_98.full_clean()
        comp_98.save()
        self.assertEqual(comp_98.kilos_netos, Decimal("98.00"))

        # 2. Caso borde: bruto == tara (100 kg == 100 kg) -> debe rechazarse
        comp_igual = ComprobanteAcopio(
            numero="REC-2026-IGUAL",
            productor=self.productor,
            tipo_producto=self.tipo_producto,
            campania=self.campania,
            fecha=date(2026, 3, 20),
            kilos_brutos=Decimal("100.00"),
            tara=Decimal("100.00"),
            porcentaje_humedad=Decimal("10.0"),
            precio_referencia=Decimal("2850.00"),
            usuario_responsable=self.acopiador,
        )
        with self.assertRaises(ValidationError):
            comp_igual.full_clean()

        # 3. Caso borde: bruto < tara (80 kg < 100 kg) -> debe rechazarse
        comp_menor = ComprobanteAcopio(
            numero="REC-2026-MENOR",
            productor=self.productor,
            tipo_producto=self.tipo_producto,
            campania=self.campania,
            fecha=date(2026, 3, 20),
            kilos_brutos=Decimal("80.00"),
            tara=Decimal("100.00"),
            porcentaje_humedad=Decimal("10.0"),
            precio_referencia=Decimal("2850.00"),
            usuario_responsable=self.acopiador,
        )
        with self.assertRaises(ValidationError):
            comp_menor.full_clean()

    def test_matriz_04_denegar_cambio_precio_acopiador_y_administracion(self):
        """Matriz P1: Intentar cambiar precio con perfil Acopiador y Administración; ambas operaciones deben negarse (403)."""
        admin_user = User.objects.create_user(
            username="admin_salta",
            email="admin_salta@saborandino.com",
            password="AdminPassword2026!",
            is_active=True,
            estado="aprobado",
            rol="administracion",
        )

        client = Client(SERVER_NAME="localhost")

        # Intento de Acopiador -> Denegado 403
        client.force_login(self.acopiador)
        self.assertEqual(client.get(reverse("acopio:precio_crear")).status_code, 403)
        self.assertEqual(
            client.post(
                reverse("acopio:precio_editar", args=[self.precio_ref.id]),
                {"tipo_producto": self.tipo_producto.id, "campania": self.campania.id, "precio_por_kg": "5000.00"},
            ).status_code,
            403,
        )

        # Intento de Administración -> Denegado 403
        client.force_login(admin_user)
        self.assertEqual(client.get(reverse("acopio:precio_crear")).status_code, 403)
        self.assertEqual(
            client.post(
                reverse("acopio:precio_editar", args=[self.precio_ref.id]),
                {"tipo_producto": self.tipo_producto.id, "campania": self.campania.id, "precio_por_kg": "5000.00"},
            ).status_code,
            403,
        )

    def test_matriz_05_anticipos_multiples_productores_y_consulta(self):
        """Matriz P2: Crear anticipos de distintos importes para productores diferentes y comprobar consultas, autor y fecha."""
        prod2 = Productor.objects.create(
            nombre_completo="Cooperativa Calchaquí",
            cuit="30-71122334-9",
            localidad="San Carlos, Salta",
        )
        client = Client(SERVER_NAME="localhost")
        client.force_login(self.gerente)

        # Anticipo 1
        client.post(
            reverse("acopio:anticipo_crear"),
            {"productor": self.productor.id, "fecha": "2026-03-01", "importe": "80000.00", "autorizado_por": "Roberto Zerpa"},
        )
        # Anticipo 2
        client.post(
            reverse("acopio:anticipo_crear"),
            {"productor": prod2.id, "fecha": "2026-03-02", "importe": "120000.00", "autorizado_por": "Roberto Zerpa"},
        )

        resp_list = client.get(reverse("acopio:anticipos_lista"))
        self.assertEqual(resp_list.status_code, 200)
        self.assertEqual(resp_list.context["anticipos"].count(), 2)

        # Consulta con filtro por productor 2
        resp_filtro = client.get(reverse("acopio:anticipos_lista"), {"q": "Cooperativa"})
        self.assertEqual(resp_filtro.context["anticipos"].count(), 1)
        self.assertEqual(resp_filtro.context["anticipos"].first().importe, Decimal("120000.00"))

    def test_matriz_06_ingreso_ultimo_dia_mes_vencimiento_30_dias_corridos(self):
        """Matriz P2: Probar ingresos el último día del mes y comprobar vencimiento a 30 días corridos."""
        # 31 de Enero de 2026 + 30 días corridos = 2 de Marzo de 2026 (2026 no es bisiesto, Feb tiene 28 días)
        fecha_ingreso = date(2026, 1, 31)
        comp = ComprobanteAcopio.objects.create(
            numero="REC-2026-ENERO31",
            productor=self.productor,
            tipo_producto=self.tipo_producto,
            campania=self.campania,
            fecha=fecha_ingreso,
            kilos_brutos=Decimal("2000.00"),
            tara=Decimal("500.00"),
            porcentaje_humedad=Decimal("10.0"),
            precio_referencia=Decimal("2850.00"),
            usuario_responsable=self.acopiador,
        )

        client = Client(SERVER_NAME="localhost")
        client.force_login(self.gerente)
        client.get(reverse("acopio:liquidacion_generar", args=[comp.id]))

        liq = Liquidacion.objects.get(comprobante=comp)
        fecha_esperada = fecha_ingreso + timedelta(days=30)
        self.assertEqual(liq.fecha_vencimiento, fecha_esperada)
        self.assertEqual(liq.fecha_vencimiento, date(2026, 3, 2))

    def test_matriz_07_no_duplicar_anticipos_imputados_en_liquidaciones(self):
        """Matriz P2: Verificar la liquidación y no duplicar anticipos imputados."""
        # Crear un anticipo de $ 50.000
        ant = Anticipo.objects.create(
            numero="ANT-2026-UNICO",
            productor=self.productor,
            fecha=date(2026, 3, 1),
            importe=Decimal("50000.00"),
            usuario_registro=self.gerente,
            autorizado_por="Roberto Zerpa",
            imputado=False,
        )

        # Comprobante 1: 1000 kg a $ 2850 = $ 2.850.000
        comp1 = ComprobanteAcopio.objects.create(
            numero="REC-2026-COMP1",
            productor=self.productor,
            tipo_producto=self.tipo_producto,
            campania=self.campania,
            fecha=date(2026, 3, 2),
            kilos_brutos=Decimal("2000.00"),
            tara=Decimal("1000.00"),
            porcentaje_humedad=Decimal("10.0"),
            precio_referencia=Decimal("2850.00"),
            usuario_responsable=self.acopiador,
        )

        # Comprobante 2: 1000 kg a $ 2850 = $ 2.850.000
        comp2 = ComprobanteAcopio.objects.create(
            numero="REC-2026-COMP2",
            productor=self.productor,
            tipo_producto=self.tipo_producto,
            campania=self.campania,
            fecha=date(2026, 3, 3),
            kilos_brutos=Decimal("2000.00"),
            tara=Decimal("1000.00"),
            porcentaje_humedad=Decimal("10.0"),
            precio_referencia=Decimal("2850.00"),
            usuario_responsable=self.acopiador,
        )

        client = Client(SERVER_NAME="localhost")
        client.force_login(self.gerente)

        # Primera liquidación: Debe descontar los $ 50.000
        client.get(reverse("acopio:liquidacion_generar", args=[comp1.id]))
        liq1 = Liquidacion.objects.get(comprobante=comp1)
        self.assertEqual(liq1.total_anticipos, Decimal("50000.00"))
        self.assertEqual(liq1.saldo_neto, Decimal("2800000.00"))

        ant.refresh_from_db()
        self.assertTrue(ant.imputado)

        # Segunda liquidación del mismo productor: NO debe descontar el anticipo nuevamente (debe ser $ 0)
        client.get(reverse("acopio:liquidacion_generar", args=[comp2.id]))
        liq2 = Liquidacion.objects.get(comprobante=comp2)
        self.assertEqual(liq2.total_anticipos, Decimal("0.00"))
        self.assertEqual(liq2.saldo_neto, Decimal("2850000.00"))

    def test_matriz_08_filtros_productor_campania_y_exportar_csv(self):
        """Matriz P1/P2: Aplicar filtros de productor/campaña, exportar la consulta y comparar su contenido con la pantalla."""
        comp = ComprobanteAcopio.objects.create(
            numero="REC-2026-CSV1",
            productor=self.productor,
            tipo_producto=self.tipo_producto,
            campania=self.campania,
            fecha=date(2026, 3, 25),
            kilos_brutos=Decimal("4000.00"),
            tara=Decimal("1000.00"),
            porcentaje_humedad=Decimal("10.0"),
            precio_referencia=Decimal("2850.00"),
            usuario_responsable=self.acopiador,
        )

        client = Client(SERVER_NAME="localhost")
        client.force_login(self.acopiador)

        # 1. Consulta en pantalla con filtros
        resp_pantalla = client.get(
            reverse("acopio:reportes"),
            {"productor": self.productor.id, "campania": self.campania.id},
        )
        self.assertEqual(resp_pantalla.status_code, 200)
        self.assertContains(resp_pantalla, "REC-2026-CSV1")
        self.assertContains(resp_pantalla, "3000")

        # 2. Descarga del archivo CSV exportado
        resp_csv = client.get(
            reverse("acopio:reportes_exportar_csv"),
            {"tipo": "recepciones", "productor": self.productor.id, "campania": self.campania.id},
        )
        self.assertEqual(resp_csv.status_code, 200)
        self.assertEqual(resp_csv["Content-Type"], "text/csv; charset=utf-8")
        csv_contenido = resp_csv.content.decode("utf-8")
        self.assertIn("REC-2026-CSV1", csv_contenido)
        self.assertIn("3000.00", csv_contenido)
        self.assertIn("Finca Las Pailas", csv_contenido)

    def test_rectificacion_autorizada_sin_borrado_silencioso(self):
        """Pág. 8 y 14: Rectificaciones autorizadas conservando el historial sin borrado."""
        comp = ComprobanteAcopio.objects.create(
            numero="REC-2026-RECTIF",
            productor=self.productor,
            tipo_producto=self.tipo_producto,
            campania=self.campania,
            fecha=date(2026, 3, 26),
            kilos_brutos=Decimal("5000.00"),
            tara=Decimal("1500.00"),
            porcentaje_humedad=Decimal("12.0"),
            precio_referencia=Decimal("2850.00"),
            usuario_responsable=self.acopiador,
        )
        self.assertEqual(comp.kilos_netos, Decimal("3500.00"))

        client = Client(SERVER_NAME="localhost")
        client.force_login(self.gerente)

        # Rectificar tara a 1200 kg con motivo justificado
        resp_rect = client.post(
            reverse("acopio:recepcion_rectificar", args=[comp.id]),
            {
                "kilos_brutos": "5000.00",
                "tara": "1200.00",
                "porcentaje_humedad": "11.0",
                "observaciones": "Báscula recalibrada",
                "motivo_rectificacion": "Error de tara de acoplado - Autorizado por Roberto Zerpa",
            },
        )
        self.assertEqual(resp_rect.status_code, 302)
        comp.refresh_from_db()
        self.assertTrue(comp.rectificado)
        self.assertEqual(comp.kilos_netos, Decimal("3800.00"))
        self.assertIn("Error de tara", comp.motivo_rectificacion)

        # Verificar que quedó registrado en el Historial de Actividades
        ultimo_evento = HistorialActividad.objects.filter(accion="RECEPCION_RECTIFICAR").first()
        self.assertIsNotNone(ultimo_evento)
        self.assertIn("REC-2026-RECTIF", ultimo_evento.descripcion)

    def test_ficha_productor_integral(self):
        """Módulo 2 (Pág. 11-12): Ficha integral del productor con todos sus comprobantes y balances."""
        client = Client(SERVER_NAME="localhost")
        client.force_login(self.acopiador)

        resp = client.get(reverse("acopio:productor_detalle", args=[self.productor.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Finca Las Pailas", resp.context["productor"].nombre_completo)
        self.assertContains(resp, "Ficha Integral de Productor")

