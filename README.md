# VITA VOLEY — Sistema de gestión académica

Aplicación web para la **Academia VITA VOLEY** (vóley formativo). Administra alumnas, asistencia, membresías, pagos, ventas, egresos y reportes Excel/PDF.

**Producción:** [vitavoley.pythonanywhere.com](https://vitavoley.pythonanywhere.com)  
**Repositorio:** [github.com/JhonHuanacuni/voley2.0](https://github.com/JhonHuanacuni/voley2.0)

---

## Tabla de contenidos

1. [Tecnologías](#tecnologías)
2. [Roles de usuario](#roles-de-usuario)
3. [Módulos del sistema](#módulos-del-sistema)
4. [Estructura del proyecto](#estructura-del-proyecto)
5. [Instalación local](#instalación-local)
6. [Base de datos](#base-de-datos)
7. [Despliegue en PythonAnywhere](#despliegue-en-pythonanywhere)
8. [Flujo Git (local ↔ producción)](#flujo-git-local--producción)
9. [Reportes y recibos PDF](#reportes-y-recibos-pdf)
10. [Zona horaria](#zona-horaria)
11. [Comandos útiles](#comandos-útiles)

---

## Tecnologías

| Componente | Detalle |
|------------|---------|
| Backend | Django 5.2 |
| Base de datos | SQLite (`db.sqlite3`) |
| Frontend | Bootstrap 4, SB Admin 2, Font Awesome |
| Excel | openpyxl |
| PDF (recibos) | pypdf + reportlab |
| QR asistencia | qrcode + Pillow |
| Idioma / hora | Español · `America/Lima` (Perú) |

### Dependencias Python

```
Django==5.2.14
openpyxl==3.1.5
pypdf==6.12.1
reportlab==4.5.1
qrcode==8.2
pillow==12.2.0
```

---

## Roles de usuario

| Rol | Acceso |
|-----|--------|
| **Administrador** | Todo: alumnas, asistencia, membresías, pagos, reportes financieros, ventas, egresos, ciclos, turnos, usuarios |
| **Secretaria** | Alumnas, asistencia, membresías, pagos y reportes básicos (sin columna PAGO MEMBRESÍA ni reporte financiero) |
| **Superusuario Django** | Tratado como administrador |

Los roles se gestionan en **Administración → Usuarios del sistema** o en `/admin/`.

---

## Módulos del sistema

### Academia

| Módulo | Ruta | Descripción |
|--------|------|-------------|
| Dashboard | `/` | KPIs: pagos del mes, egresos, ventas, gráfica de asistencias por turno |
| Alumnas | `/students/` | Registro completo (DNI, ciclo, turno, apoderado, uniforme, etc.). Filtros por nombre, ciclo y turno. Paginación 10/20/50 |
| Asistencia | `/attendance/` | Registro diario por turno. Buscador desde 3 caracteres. QR por alumna |
| Membresías | `/memberships/` | Periodos de membresía con monto, estado (deuda/completada), renovación |
| Pagos | `/memberships/payments/` | Historial global de pagos. Recibo PDF y envío por WhatsApp |
| Retiradas | `/students/retired/` | Alumnas dadas de baja con opción de reactivar |
| Reportes | `/reports/` | Exportaciones Excel (ver sección [Reportes](#reportes-y-recibos-pdf)) |

### Administración (solo admin)

| Módulo | Ruta | Descripción |
|--------|------|-------------|
| Ciclos | `/cycles/` | Categorías etarias (Niñas, Adolescentes, Juvenil, etc.) |
| Turnos | `/shifts/` | Horarios y días activos por turno |
| Ventas | `/sales/` | Uniformes y productos: nombre, turno, talla, precio, observación. Recibo PDF |
| Egresos | `/expenses/` | Gastos: concepto, proveedor, monto, medio de pago |
| Usuarios | `/users/` | Crear/editar usuarios del sistema con rol |

---

## Estructura del proyecto

```
voley2.0/
├── academia/              # Configuración Django (settings, urls, wsgi)
├── core/                  # App principal
│   ├── models.py          # Student, Membership, Payment, Sale, Expense, Shift, Cycle…
│   ├── views*.py          # Vistas por módulo
│   ├── forms.py           # Formularios
│   ├── receipt_pdf.py     # Generación de recibos PDF
│   ├── attendance_matrix_export.py   # Excel asistencia mensual
│   ├── financial_report_export.py    # Excel reporte financiero
│   ├── attendance_report.py          # Datos gráfica dashboard
│   ├── time_utils.py      # Fechas en hora Perú
│   ├── migrations/        # Migraciones de base de datos
│   ├── templates/core/    # Plantillas HTML
│   └── static/            # CSS, JS, imágenes, plantillas PDF
│       ├── template Boleta/          # Recibo pago membresía
│       └── template Venta/           # Nota de venta
├── db.sqlite3             # Base de datos (versionada en este proyecto)
├── manage.py
└── README.md
```

---

## Instalación local

### Requisitos

- Python 3.10+ (probado con 3.14)
- Git

### Pasos

```bash
# Clonar
git clone https://github.com/JhonHuanacuni/voley2.0.git
cd voley2.0

# Entorno virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate

# Dependencias
pip install Django==5.2.14 openpyxl pypdf reportlab qrcode pillow

# Migraciones (por si faltan tablas)
python manage.py migrate

# Usuario admin (solo la primera vez)
python manage.py createsuperuser

# Servidor local
python manage.py runserver
```

Abrir: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Base de datos

El proyecto usa **SQLite** en `db.sqlite3`.

En este repositorio la base de datos **sí se versiona en Git**. El flujo acordado es:

1. Descargar `db.sqlite3` desde PythonAnywhere cuando quieras sincronizar producción → local.
2. Hacer cambios en local y commitear (código + BD si aplica).
3. En PythonAnywhere hacer `git pull` para recibir la misma BD.

> Si en el futuro prefieres no versionar la BD, descomenta las líneas de `db.sqlite3` en `.gitignore` y sácalo del repositorio con `git rm --cached db.sqlite3`.

---

## Despliegue en PythonAnywhere

### Configuración inicial (una sola vez)

1. Clonar en `~/voley2.0`
2. Crear virtualenv `venv` e instalar dependencias
3. En la pestaña **Web**:
   - **Source code:** `/home/TU_USUARIO/voley2.0`
   - **Virtualenv:** `/home/TU_USUARIO/.virtualenvs/venv`
   - **WSGI:** apuntar a `academia/wsgi.py`
4. **Static files:** `/static/` → `/home/TU_USUARIO/voley2.0/staticfiles`
5. Ejecutar `python manage.py collectstatic` y `python manage.py migrate`

### Actualizar producción (cada deploy)

```bash
cd ~/voley2.0
workon venv

# Si git se queja por db.sqlite3 (cambios locales en PA):
git restore db.sqlite3

git pull
python manage.py migrate
```

Luego en PythonAnywhere: pestaña **Web** → botón verde **Reload**.

---

## Flujo Git (local ↔ producción)

### Desarrollar en local

```bash
git add .
git commit -m "Descripción del cambio"
git push origin main
```

### Publicar en PythonAnywhere

```bash
cd ~/voley2.0
workon venv
git restore db.sqlite3    # solo si git pull falla por db.sqlite3
git pull
python manage.py migrate
# Web → Reload
```

### Sincronizar BD de producción a local

1. En PythonAnywhere: descargar `/home/TU_USUARIO/voley2.0/db.sqlite3`
2. Reemplazar el archivo local `db.sqlite3`
3. Commit y push si quieres que producción y repo queden alineados

### Error común: `db.sqlite3 would be overwritten by merge`

Significa que hay cambios locales en PA que Git no puede mezclar. Solución:

```bash
git restore db.sqlite3
git pull
python manage.py migrate
```

Como la BD del repo viene de producción (descargada antes del commit), no hace falta respaldo extra.

---

## Reportes y recibos PDF

### Reportes Excel (`/reports/`)

| Reporte | Descripción |
|---------|-------------|
| **Alumnas** | Listado completo exportable |
| **Asistencia mensual** | Matriz día a día (A/T/F). Columna **PAGO MEMBRESÍA** (solo admin): verde si pagó, rojo si debe |
| **Matrículas del mes** | Inscripciones del periodo |
| **Pagos** | Historial de pagos de membresía |
| **Ingresos y egresos** | Tabla de egresos del mes + resumen: Mes anterior, Ingresos, Egresos, Utilidad |

#### Columna PAGO MEMBRESÍA (asistencia mensual)

**Verde (pagó todo):**
```
TOTAL: S/ 200.00 - 30/06/2026
S/ 80.00 - 06/06/2026
S/ 100.00 - 15/06/2026
S/ 20.00 - 20/06/2026
```

**Rojo (debe):**
```
TOTAL: S/ 200.00 - 30/06/2026
S/ 80.00 - 06/06/2026
Pendiente: S/ 120.00
```

### Recibos PDF

| Tipo | Plantilla | Botón |
|------|-----------|-------|
| Pago membresía | `core/static/template Boleta/plantilla Voley Vita.pdf` | Recibo / Enviar (WhatsApp) |
| Venta | `core/static/template Venta/plantilla Voley Vita Ventas.pdf` | Recibo en módulo Ventas |

Generados en `core/receipt_pdf.py`.

---

## Zona horaria

Configurado en `academia/settings.py`:

```python
TIME_ZONE = 'America/Lima'
USE_TZ = True
```

Fechas de ventas, reportes y recibos usan **hora de Perú** (`timezone.localtime()` / `timezone.localdate()`).

---

## Comandos útiles

```bash
# Ver migraciones pendientes
python manage.py showmigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recolectar estáticos (producción)
python manage.py collectstatic --noinput

# Shell Django
python manage.py shell

# Verificar proyecto
python manage.py check
```

---

## Modelos principales

| Modelo | Uso |
|--------|-----|
| `Student` | Alumna: datos personales, turno, ciclo, apoderado, cuota mensual |
| `Membership` | Periodo de membresía con monto y fechas inicio/fin |
| `Payment` | Pago vinculado a membresía y alumna |
| `Attendance` | Asistencia diaria (presente / tarde / falta) |
| `Shift` | Turno con horario y días activos |
| `Cycle` | Categoría / ciclo etario |
| `Sale` | Venta de productos (uniformes, etc.) |
| `Expense` | Egreso / gasto |
| `UserProfile` | Rol del usuario (admin / secretaria) |

---

## Contacto academia

**ACADEMIA VITA VOLEY**  
Av. San Juan 741, San Juan de Miraflores  
@VOLEY VITA · 908 935 924

---

## Licencia

Proyecto privado — uso interno de Academia VITA VOLEY.
