# SMS Rental Platform

Plataforma de alquiler de numeros telefonicos para verificacion SMS, usando DaisySMS como proveedor.

## Requisitos

- Docker y Docker Compose
- Python 3.11+ (para desarrollo local)
- PostgreSQL 15+
- Redis 7+ (para cache)

## Inicio Rapido con Docker

1. **Clonar y configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus valores (API key de DaisySMS, etc.)
```

2. **Iniciar servicios:**
```bash
docker-compose up -d
```

3. **Crear superusuario (admin):**
```bash
docker-compose exec web python manage.py createsuperuser
```

4. **Configurar tasa de cambio inicial:**
   - Acceder a http://localhost:8000/admin/
   - Ir a "Tasas de cambio" y crear una con el valor deseado (ej: 4800 CUP por USD)

5. **Acceder a la API:**
   - API: http://localhost:8000/api/
   - Admin: http://localhost:8000/admin/
   - Health: http://localhost:8000/health/

## Desarrollo Local

1. **Crear entorno virtual:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env
```

4. **Ejecutar migraciones:**
```bash
python manage.py migrate
```

5. **Crear superusuario:**
```bash
python manage.py createsuperuser
```

6. **Ejecutar servidor de desarrollo:**
```bash
python manage.py runserver
```

## Estructura del Proyecto

```
smsproject/
├── config/                 # Configuracion Django
│   ├── settings.py        # Settings principales
│   ├── urls.py            # URLs raiz
│   └── wsgi.py
├── apps/
│   ├── users/             # Usuarios y autenticacion
│   ├── accounts/          # Cuentas, balance, transacciones
│   ├── services/          # Integracion DaisySMS
│   └── rentals/           # Alquiler de numeros
├── docs/
│   └── API_DOCS.md        # Documentacion de API
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Variables de Entorno

| Variable | Descripcion | Default |
|----------|-------------|---------|
| DEBUG | Modo debug | False |
| SECRET_KEY | Clave secreta Django | - |
| ALLOWED_HOSTS | Hosts permitidos | localhost |
| DB_NAME | Nombre de la BD | smsproject |
| DB_USER | Usuario de BD | postgres |
| DB_PASSWORD | Password de BD | postgres |
| DB_HOST | Host de BD | localhost |
| DAISY_SMS_API_KEY | API Key de DaisySMS | - |
| DEFAULT_EXCHANGE_RATE_CUP_PER_USD | Tasa de cambio default | 4800 |
| GOOGLE_OAUTH_CLIENT_ID | Client ID de Google | - |
| GOOGLE_OAUTH_CLIENT_SECRET | Secret de Google | - |

## API Simplificada

La API de alquileres usa solo **3 endpoints**:

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | /api/rentals/ | Crear nuevo alquiler |
| GET | /api/rentals/ | Listar alquileres (polling integrado) |
| POST | /api/rentals/{id}/cancel/ | Cancelar alquiler |

Ver documentacion completa en [docs/API_DOCS.md](docs/API_DOCS.md)

### Otros Endpoints Principales

- `POST /api/auth/registration/` - Registro
- `POST /api/auth/login/` - Login
- `GET /api/account/balance/` - Ver balance
- `GET /api/services/` - Listar servicios disponibles

## Arquitectura

### Polling desde Frontend (Sin Celery)

El sistema usa un modelo de **polling** donde el frontend es responsable de:

1. **Crear alquiler**: `POST /api/rentals/`
2. **Polling cada 3-5 segundos**: `GET /api/rentals/`
3. **Cancelar si necesario**: `POST /api/rentals/{id}/cancel/`

### Flujo Simplificado

```
┌─────────────┐     POST /api/rentals/      ┌─────────────┐
│   Frontend  │ ──────────────────────────► │   Backend   │
│             │ ◄────────────────────────── │             │
│             │     rental created          │             │
│             │                             │             │
│             │     GET /api/rentals/       │             │     get_sms_status()
│             │ ──────────────────────────► │             │ ──────────────────► DaisySMS
│   (polling  │ ◄────────────────────────── │  (syncs &   │ ◄──────────────────
│   cada 3-5s)│     rentals + SMS status    │  processes) │
│             │                             │             │
│             │     [si expira sin SMS]     │             │
│             │ ◄────────────────────────── │             │
│             │     refund automático       │             │
└─────────────┘                             └─────────────┘
```

### Procesamiento en GET /api/rentals/

En cada peticion GET, el backend:

1. Lista todos los alquileres del usuario
2. Para cada alquiler ACTIVE, consulta DaisySMS
3. Si llego SMS → Guarda en BD, cambia status a SMS_RECEIVED
4. Si expiro sin SMS → Procesa reembolso automatico, status = REFUNDED
5. Devuelve array completo con toda la info

### Limites

- **5 alquileres activos** por usuario simultaneamente
- **Rate limiting** por endpoint (ver API_DOCS.md)
- **Cache de servicios** por 5 minutos

## Flujo de Uso

```
1. Usuario se registra/login
2. Admin agrega credito al usuario (en CUP)
3. Usuario ve servicios disponibles con precios
4. Usuario crea alquiler (POST /api/rentals/)
5. Frontend hace polling (GET /api/rentals/ cada 3-5s)
   - Backend sincroniza con DaisySMS
   - Si llega SMS → Frontend lo muestra
   - Si expira → Backend reembolsa automaticamente
6. (Opcional) Usuario cancela antes de expirar
```

## Licencia

MIT
