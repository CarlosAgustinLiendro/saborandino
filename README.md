# Sabor Andino S.R.L. · Plataforma Web de Gestión

Plataforma web integral de acopio, gestión de inventario, catálogo de especias y distribución regional de **Sabor Andino S.R.L.** (Valles Calchaquíes, Salta).

Desarrollada para la cátedra **Práctica Profesional II** (Instituto Superior del Milagro N° 8207) a partir del diseño, flujos y funcionalidades de la aplicación móvil de referencia, adaptada con formato y estándares web modernos.

---

## Características Principales

1. **Diseño Web Moderno y Adaptativo (Desktop-First)**:
   - Identidad visual oficial: colores verde calchaquí (`#3e6531`), crema (`#FAF8F3`), y naranja acento (`#E89B3C`).
   - Logotipo oficial e ilustración panorámica de los Valles Calchaquíes.
   - **Modo Oscuro y Claro**: alternancia instantánea sin recarga con persistencia en `localStorage`.

2. **Panel de Gestión Central (Dashboard)**:
   - Métricas clave (KPIs): Total de productos, stock en unidades, categorías activas, solicitudes de acceso.
   - Centro interactivo **"¿Qué necesitás gestionar?"**:
     - **Productos**: Catálogo maestro, fichas técnicas, lotes y existencias.
     - **Pedidos**: Gestión de órdenes mayoristas y estados de preparación.
     - **Proveedores / Acopio**: Padrón de productores agrícolas de Cachi, Cafayate, Molinos y San Carlos.
     - **Cobranzas**: Liquidaciones por acopio, comprobantes e imputación de anticipos.
     - **Depósito**: Control de silos en Cachi, almacenamiento en Salta y temperaturas.
     - **Entregas**: Logística de transporte y ruteo regional hacia el NOA.

3. **Catálogo Maestro de Productos**:
   - Selector dinámico de visualización: **Vista en Tarjetas** vs **Vista en Tabla**.
   - Búsqueda en tiempo real por nombre, código y procedencia.
   - Filtro interactivo por familias de categorías.
   - **Modal de Detalle Rápido**: Visualización completa de características, origen, vencimiento y precio.
   - **Modal de Eliminación Segura**: Confirmación con advertencia de impacto.
   - Formulario de alta y edición con previsualización en vivo de ilustraciones de especias y condimentos.

4. **Gestión de Perfil de Usuario**:
   - Selector interactivo de avatares: *Neutral*, *Hombre*, *Mujer*.
   - Edición de nombre y apellido con validación estricta.
   - Roles diferenciados: Socio Gerente / Administrador vs Operador de Acopio.

5. **Ajustes y Seguridad**:
   - Switch de tema de apariencia (Modo oscuro / claro).
   - Switch de notificaciones push del sistema.
   - Modal de cambio y restablecimiento de contraseña.
   - Modal interactivo con los **Términos y Condiciones** de Sabor Andino S.R.L.
   - Canales de atención directa: WhatsApp (+54 9 387 555-1234), Correo (soporte@saborandino.com) y Teléfono.
   - Acordeón de Preguntas Frecuentes (FAQ).

---

## Puesta en Marcha

### Opción 1: Ejecución Local Rápida (Entorno Virtual Python)

1. Activar el entorno virtual o instalar requerimientos:
   ```powershell
   .\.venv\Scripts\activate
   # O instalar si es necesario: pip install -r requirements.txt
   ```
2. Aplicar migraciones y cargar datos de demostración:
   ```powershell
   python manage.py migrate
   python manage.py crear_datos_iniciales
   ```
3. Iniciar el servidor web:
   ```powershell
   python manage.py runserver
   ```
4. Abrir en el navegador: [http://localhost:8000](http://localhost:8000)

### Opción 2: Despliegue con Docker y PostgreSQL

```powershell
docker compose up --build -d
```
Abrir en el navegador: [http://localhost:8000](http://localhost:8000)

---

## Credenciales de Acceso Precargadas

| Rol | Usuario | Contraseña | Correo Electrónico |
| :--- | :--- | :--- | :--- |
| **Administrador** | `carlos` | `SaborAndino2026!` | `liendrocarlosagustin@gmail.com` |
| **Operador** | `operador` | `SaborAndino2026!` | `operador@saborandino.com` |

---

## Verificación de Pruebas Automatizadas

Para ejecutar la suite completa de pruebas unitarias y de integración de Django:
```powershell
python manage.py test
```
