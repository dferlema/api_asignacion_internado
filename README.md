# 🏥 API — Sistema de Asignación Prioritaria de Internado
### Backend Django REST + XGBoost + PostgreSQL + Redis
### Arquitectura en 6 Capas — Compatible con ERP inno-fact

---

## 📐 Arquitectura en 6 Capas (estándar ERP)

```
Capa 1 │ urls.py        → Enrutamiento: define qué URL ejecuta qué vista
Capa 2 │ views.py       → HTTP: recibe request, valida con Form, delega al Controller
Capa 3 │ controllers.py → Orquestación: llama a Business, serializa, retorna respuesta
Capa 4 │ business.py    → Lógica de negocio: consultas, escrituras con @transaction.atomic
Capa 5 │ serializers.py → Serialización: transforma modelos a JSON y viceversa
Capa 6 │ forms.py       → Validación: valida datos de entrada con Django Forms
```

**Regla de oro:** El view NO tiene lógica de negocio. El business NO conoce el request HTTP.

---

## 🗂️ Estructura del Proyecto

```
internado_api_v2/
│
├── internado/              # Configuración central
│   ├── settings.py         # Django + JWT + Redis + Middleware
│   ├── urls.py             # Rutas principales
│   └── wsgi.py
│
├── helpers/                # Utilidades transversales del ERP
│   ├── my_model.py         # ← ModelBase: soft delete + auditoría automática
│   ├── middleware.py       # ← ThreadLocal: captura request en todo el sistema
│   ├── base_views.py       # ← VistaAutenticada / VistaPublica / VistaOpcional
│   ├── response_helper.py  # ← Formato estándar: success/message/data
│   ├── auth_helper.py      # ← JWT HttpOnly Cookies + Rate Limiting
│   └── error_helper.py     # ← Mensajes amigables para errores de BD
│
├── estudiantes/            # App: gestión de estudiantes (6 capas)
│   ├── models.py           # Hereda ModelBase
│   ├── forms.py            # Validación (Capa 6)
│   ├── serializers.py      # Serialización (Capa 5)
│   ├── business.py         # Lógica de negocio (Capa 4)
│   ├── controllers.py      # Orquestación (Capa 3)
│   ├── views.py            # HTTP (Capa 2)
│   └── urls.py             # Enrutamiento (Capa 1)
│
├── ranking/                # App: algoritmo XGBoost (6 capas)
│   ├── forms.py
│   ├── business.py         # XGBoost + asignación (@transaction.atomic)
│   ├── controllers.py
│   ├── views.py
│   └── urls.py
│
├── plazas/                 # App: gestión de plazas (6 capas)
│   ├── models.py           # Hereda ModelBase
│   ├── forms.py
│   ├── serializers.py
│   ├── business.py
│   ├── controllers.py
│   ├── views.py
│   └── urls.py
│
├── docker-compose.yml      # PostgreSQL 16.2 + Redis 7.2 en contenedores
├── manage.py
├── requirements.txt        # Versiones validadas con Python 3.13
└── .env                    # Variables de entorno (no subir al repositorio)
```

---

## 🐳 Requisitos previos

| Herramienta | Versión mínima | Notas |
|---|---|---|
| Python | 3.13+ | Validado con esta versión |
| Docker Desktop | Cualquier versión reciente | Para PostgreSQL y Redis |
| Git | Cualquier versión | Para control de versiones |
| WSL 2 | — | Requerido por Docker en Windows |

---

## ⚙️ Instalación paso a paso (Windows)

### 1. Levantar PostgreSQL y Redis con Docker

Crea el archivo `docker-compose.yml` en la raíz del proyecto:

```yaml
services:
  postgres:
    image: postgres:16.2
    container_name: internado_postgres
    restart: always
    environment:
      POSTGRES_DB:       innotech_db
      POSTGRES_USER:     postgres
      POSTGRES_PASSWORD: postgres123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7.2
    container_name: internado_redis
    restart: always
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

```powershell
docker compose up -d
docker compose ps    # Verificar que ambos estén en estado running
```

### 2. Crear y activar el entorno virtual

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

> Si PowerShell bloquea la ejecución: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### 3. Instalar dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crear el archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=clave-secreta-proyecto-internado-cambiar-en-produccion
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=innotech_db
DB_USER=postgres
DB_PASSWORD=postgres123
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/1

CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### 5. Aplicar migraciones

```powershell
python manage.py makemigrations estudiantes
python manage.py makemigrations plazas
python manage.py migrate
```

### 6. Crear superusuario

```powershell
python manage.py createsuperuser
```

### 7. Iniciar el servidor

```powershell
python manage.py runserver
```

---

## 🔁 Comandos de uso diario

```powershell
# Levantar contenedores Docker
docker compose up -d

# Activar entorno virtual
venv\Scripts\Activate.ps1

# Iniciar servidor
python manage.py runserver

# Detener servidor: CTRL + C

# Detener contenedores (datos conservados)
docker compose stop
```

---

## 🔗 Endpoints de la API

### 🎓 Estudiantes `/api/v1/estudiantes/`
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/v1/estudiantes/` | Listar todos los estudiantes activos |
| POST | `/api/v1/estudiantes/` | Registrar nuevo estudiante |
| GET | `/api/v1/estudiantes/{id}/` | Ver detalle |
| PUT | `/api/v1/estudiantes/{id}/` | Actualizar |
| DELETE | `/api/v1/estudiantes/{id}/` | Soft delete |
| GET | `/api/v1/estudiantes/habilitados/` | Solo los habilitados |
| GET | `/api/v1/estudiantes/{id}/validar-requisitos/` | Validar requisitos |

### 🏆 Ranking IA `/api/v1/ranking/`
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/v1/ranking/generar/` | Ejecutar XGBoost (sin guardar) |
| POST | `/api/v1/ranking/asignar/` | Asignar plazas y guardar en BD |
| GET | `/api/v1/ranking/consultar/?periodo=2024-1` | Consultar asignaciones |

### 🏥 Plazas `/api/v1/plazas/`
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/v1/plazas/` | Listar todas las plazas |
| POST | `/api/v1/plazas/` | Crear nueva plaza |
| GET | `/api/v1/plazas/{id}/` | Ver detalle |
| PUT | `/api/v1/plazas/{id}/` | Actualizar |
| DELETE | `/api/v1/plazas/{id}/` | Soft delete |
| GET | `/api/v1/plazas/disponibles/` | Solo disponibles |
| GET | `/api/v1/plazas/asignaciones/` | Ver asignaciones |

### 🔐 Autenticación JWT
| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/api/v1/auth/refresh/` | Refrescar token de acceso |
| POST | `/api/v1/auth/verify/` | Verificar validez del token |

---

## 📖 Documentación interactiva

```
http://localhost:8000/api/docs/   → Swagger UI
http://localhost:8000/api/redoc/  → ReDoc
http://localhost:8000/admin/      → Panel de administración
```

---

## 🔒 Seguridad implementada

| Característica | Implementación |
|---|---|
| JWT HttpOnly Cookies | SimpleJWT 5.4.0 — protección XSS |
| Rate Limiting | 5 intentos / 5 min por IP — Redis |
| Soft Delete | ModelBase.delete() — nunca borra físicamente |
| Auditoría automática | user_create, date_create, ip_create en todos los modelos |
| Transacciones | @transaction.atomic en toda escritura |
| CORS | django-cors-headers con CORS_ALLOW_CREDENTIALS=True |

---

## 📦 Stack tecnológico

| Tecnología | Versión | Notas |
|---|---|---|
| Python | 3.13+ | Validado en Windows 10/11 |
| Django | **4.2.8** | Versión exacta del ERP |
| Django REST Framework | **3.14.0** | Versión exacta del ERP |
| SimpleJWT | **5.4.0** | Versión exacta del ERP |
| drf-spectacular | **0.27.0** | Versión exacta del ERP |
| PostgreSQL | 16.2 (Docker) | Contenedor — sin instalación local |
| Redis | 7.2 (Docker) | Contenedor — sin instalación local |
| XGBoost | 2.1.3 | Compatible con Python 3.13 |
| scikit-learn | 1.6.1 | Compatible con Python 3.13 |
| numpy | 2.2.3 | Compatible con Python 3.13 |
| pandas | 2.2.3 | Compatible con Python 3.13 |
| psycopg2-binary | 2.9.10 | Compatible con Python 3.13 |

**Todas las tecnologías son 100% Open Source.**

---

## 🔄 Formato de respuesta estándar

Todas las respuestas de la API siguen el mismo formato:

```json
// Éxito
{ "success": true, "message": "Operación completada.", "data": { ... } }

// Error de validación
{ "success": false, "message": "Datos inválidos.", "errors": { "campo": ["Error"] } }

// Error general
{ "success": false, "message": "Descripción del error." }
```

---

## ⚠️ Notas importantes

- El archivo `.env` **nunca debe subirse al repositorio**. Agrega `.env` a tu `.gitignore`.
- Las imágenes Docker `redis:7.1` y `postgres:16` no están disponibles en Docker Hub. Usar `redis:7.2` y `postgres:16.2`.
- `scikit-learn==1.4.2` y `numpy==1.26.4` no son compatibles con Python 3.13. Usar las versiones indicadas en este archivo.
