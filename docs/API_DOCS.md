# SMS Rental Platform - API Documentation

## Base URL
```
http://localhost:8000/api
```

## Autenticacion
Todos los endpoints (excepto los de auth y health) requieren autenticacion JWT:
```
Authorization: Bearer <token_jwt>
```

---

## 1. HEALTH CHECK

### Health Check
```
GET /health/

Response (200 OK):
{
  "status": "ok",
  "service": "SMS Rental Platform"
}
```

### API Root
```
GET /api/

Response (200 OK):
{
  "service": "SMS Rental Platform API",
  "version": "1.0.0",
  "endpoints": { ... }
}
```

---

## 2. AUTENTICACION

### Registro de Usuario
```
POST /api/auth/registration/

Body:
{
  "email": "usuario@ejemplo.com",
  "password1": "contraseña_segura_123",
  "password2": "contraseña_segura_123",
  "first_name": "Juan",        // opcional
  "last_name": "Perez"         // opcional
}

Response (201 Created):
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "first_name": "Juan",
    "last_name": "Perez",
    "full_name": "Juan Perez",
    "date_joined": "2025-02-01T10:00:00Z",
    "is_staff": false
  }
}

Errores:
400: Email ya existe / Passwords no coinciden
```

### Login
```
POST /api/auth/login/

Body:
{
  "email": "usuario@ejemplo.com",
  "password": "contraseña_segura_123"
}

Response (200 OK):
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    ...
  }
}

Errores:
400: Credenciales invalidas
```

### Logout
```
POST /api/auth/logout/
Authorization: Bearer <token>

Response (200 OK):
{
  "detail": "Successfully logged out."
}
```

### Refrescar Token
```
POST /api/auth/token/refresh/

Body:
{
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}

Response (200 OK):
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Obtener Usuario Actual
```
GET /api/auth/user/
Authorization: Bearer <token>

Response (200 OK):
{
  "id": 1,
  "email": "usuario@ejemplo.com",
  "first_name": "Juan",
  "last_name": "Perez",
  "full_name": "Juan Perez",
  "date_joined": "2025-02-01T10:00:00Z",
  "is_staff": false
}
```

### Actualizar Perfil
```
PATCH /api/users/profile/
Authorization: Bearer <token>

Body:
{
  "first_name": "Juan Carlos",
  "last_name": "Perez Garcia"
}

Response (200 OK):
{
  "id": 1,
  "email": "usuario@ejemplo.com",
  "first_name": "Juan Carlos",
  "last_name": "Perez Garcia",
  ...
}
```

---

## 3. CUENTA Y CREDITO

### Obtener Balance
```
GET /api/account/balance/
Authorization: Bearer <token>

Response (200 OK):
{
  "balance_cup": "12000.00",
  "balance_usd": "2.5000",
  "exchange_rate": "4800.00",
  "currency": "CUP"
}
```

### Obtener Tasa de Cambio
```
GET /api/account/exchange-rate/

Response (200 OK):
{
  "rate_cup_per_usd": "4800.00",
  "description": "1 USD = 4800.00 CUP",
  "last_updated": "2025-02-01T09:00:00Z"
}
```

### Historial de Transacciones
```
GET /api/account/transactions/
Authorization: Bearer <token>

Query Params:
- page: Numero de pagina (default: 1)

Response (200 OK):
{
  "count": 25,
  "next": "http://localhost:8000/api/account/transactions/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "type": "RENT",
      "type_display": "Alquiler de numero",
      "amount_usd": "-0.2500",
      "amount_cup": "-1200.00",
      "balance_after_cup": "10800.00",
      "description": "Alquiler WhatsApp: +13476711222",
      "rental_phone": "+13476711222",
      "created_at": "2025-02-01T10:00:00Z"
    },
    {
      "id": 2,
      "type": "REFUND",
      "type_display": "Reembolso",
      "amount_usd": "0.2500",
      "amount_cup": "1200.00",
      "balance_after_cup": "12000.00",
      "description": "Reembolso automatico: +13476711222 (expirado sin SMS)",
      "rental_phone": "+13476711222",
      "created_at": "2025-02-01T10:15:00Z"
    }
  ]
}
```

### Agregar Credito (ADMIN ONLY)
```
POST /api/account/admin/users/{user_id}/add-credit/
Authorization: Bearer <token_admin>

Body:
{
  "amount_cup": 5000,
  "reason": "Deposito efectivo"   // opcional
}

Response (200 OK):
{
  "user_id": 1,
  "user_email": "usuario@ejemplo.com",
  "previous_balance_cup": "12000.00",
  "new_balance_cup": "17000.00",
  "amount_added_cup": "5000.00",
  "message": "Credito añadido exitosamente a usuario@ejemplo.com"
}

Errores:
403: No eres admin
404: Usuario no existe
```

---

## 4. SERVICIOS

### Listar Servicios Disponibles
```
GET /api/services/
Authorization: Bearer <token>

Query Params:
- country: Codigo pais (ej: "187" para USA)
- service_code: Filtrar por codigo (ej: "wa")
- available: "true" para mostrar solo con numeros disponibles

Response (200 OK):
{
  "services": [
    {
      "service_code": "wa",
      "name": "WhatsApp",
      "price_usd": "0.2500",
      "price_cup": "1200.00",
      "available_numbers": 45,
      "supports_multiple_sms": false,
      "country": "187",
      "country_name": "USA"
    },
    {
      "service_code": "go",
      "name": "Google",
      "price_usd": "0.3000",
      "price_cup": "1440.00",
      "available_numbers": 12,
      "supports_multiple_sms": true,
      "country": "187",
      "country_name": "USA"
    }
  ],
  "exchange_rate": "4800.00",
  "total": 25
}

Errores:
503: DaisySMS API no disponible
```

---

## 5. ALQUILER DE NUMEROS (API Simplificada)

La API de alquileres ha sido simplificada a solo **3 endpoints**:

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | /api/rentals/ | Crear nuevo alquiler |
| GET | /api/rentals/ | Listar todos los alquileres (con polling integrado) |
| POST | /api/rentals/{id}/cancel/ | Cancelar alquiler |

### Alquilar un Numero
```
POST /api/rentals/
Authorization: Bearer <token>

Body:
{
  "service_code": "wa",
  "max_price_usd": 0.50,    // opcional - precio maximo
  "country": "187"          // opcional - default USA
}

Response (201 Created):
{
  "id": 1,
  "daisy_rental_id": 999999,
  "phone": "+13476711222",
  "service_code": "wa",
  "service_name": "WhatsApp",
  "status": "ACTIVE",
  "status_display": "Activo - Esperando SMS",
  "price_usd": "0.2500",
  "price_cup": "1200.00",
  "rented_at": "2025-02-01T10:00:00Z",
  "expires_at": "2025-02-01T10:15:00Z",
  "remaining_time_seconds": 900,
  "has_sms": false,
  "sms": [],
  "refunded": false,
  "new_balance_cup": "10800.00"
}

Errores:
400: Saldo insuficiente
400: No hay numeros disponibles
400: Precio excede el maximo
400: Maximo 5 alquileres activos permitidos
404: Servicio no disponible
503: Error de DaisySMS
```

**Limite de alquileres activos**: Maximo 5 alquileres activos simultaneos por usuario.

### Listar Alquileres (con Polling Integrado)
```
GET /api/rentals/
Authorization: Bearer <token>

Query Params:
- status: ACTIVE, SMS_RECEIVED, EXPIRED, CANCELLED, REFUNDED (o "all" para todos)
- limit: Numero de resultados (default: 50)
- offset: Offset para paginacion (default: 0)

Response (200 OK):
{
  "rentals": [
    {
      "id": 1,
      "daisy_rental_id": 999999,
      "phone": "+13476711222",
      "service_code": "wa",
      "service_name": "WhatsApp",
      "status": "ACTIVE",
      "status_display": "Activo - Esperando SMS",
      "price_cup": "1200.00",
      "price_usd": "0.2500",
      "rented_at": "2025-02-01T10:00:00Z",
      "expires_at": "2025-02-01T10:15:00Z",
      "remaining_time_seconds": 450,
      "has_sms": false,
      "sms": [],
      "refunded": false
    },
    {
      "id": 2,
      "daisy_rental_id": 999998,
      "phone": "+13476711333",
      "service_code": "go",
      "service_name": "Google",
      "status": "SMS_RECEIVED",
      "status_display": "SMS Recibido",
      "price_cup": "1440.00",
      "price_usd": "0.3000",
      "rented_at": "2025-02-01T09:50:00Z",
      "expires_at": "2025-02-01T10:05:00Z",
      "remaining_time_seconds": 0,
      "has_sms": true,
      "sms": [
        {
          "id": 1,
          "code": "123456",
          "text": "Your Google verification code is 123456",
          "received_at": "2025-02-01T09:55:00Z",
          "created_at": "2025-02-01T09:55:00Z"
        }
      ],
      "refunded": false
    }
  ],
  "balance_cup": "10800.00",
  "total": 2,
  "limit": 50,
  "offset": 0
}
```

**Comportamiento del Polling**:
- El endpoint sincroniza automaticamente con DaisySMS para cada alquiler ACTIVE
- Si llega un SMS, se guarda y el status cambia a SMS_RECEIVED
- Si el alquiler expira sin SMS, se procesa el reembolso automaticamente
- El response incluye `refund_amount_cup` y `new_balance_cup` cuando se procesa un reembolso

**Response con Reembolso Automatico**:
```json
{
  "rentals": [
    {
      "id": 1,
      "status": "REFUNDED",
      "status_display": "Reembolsado",
      "remaining_time_seconds": 0,
      "has_sms": false,
      "sms": [],
      "refunded": true,
      "refund_amount_cup": "1200.00",
      "new_balance_cup": "12000.00"
    }
  ],
  "balance_cup": "12000.00",
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### Cancelar Alquiler
```
POST /api/rentals/{id}/cancel/
Authorization: Bearer <token>

Response (200 OK):
{
  "rental_id": 1,
  "status": "REFUNDED",
  "status_display": "Reembolsado",
  "refunded": true,
  "refund_amount_cup": "1200.00",
  "new_balance_cup": "12000.00",
  "message": "Alquiler cancelado y reembolsado exitosamente"
}

Errores:
400: No se puede cancelar (ya tiene SMS o no esta activo)
404: Alquiler no encontrado
503: Error de DaisySMS
```

**Nota**: Solo se pueden cancelar alquileres ACTIVE que no hayan recibido SMS.

---

## 6. ADMIN ENDPOINTS

### Listar Usuarios
```
GET /api/users/admin/users/
Authorization: Bearer <token_admin>

Query Params:
- email: Filtrar por email

Response (200 OK):
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "email": "usuario@ejemplo.com",
      "first_name": "Juan",
      "last_name": "Perez",
      "full_name": "Juan Perez",
      "date_joined": "2025-02-01T10:00:00Z",
      "is_staff": false
    }
  ]
}
```

### Detalle de Usuario
```
GET /api/users/admin/users/{user_id}/
Authorization: Bearer <token_admin>

Response (200 OK):
{
  "id": 1,
  "email": "usuario@ejemplo.com",
  "first_name": "Juan",
  "last_name": "Perez",
  "full_name": "Juan Perez",
  "date_joined": "2025-02-01T10:00:00Z",
  "is_staff": false
}
```

### Balance DaisySMS (Admin)
```
GET /api/services/admin/daisy-balance/
Authorization: Bearer <token_admin>

Response (200 OK):
{
  "balance_usd": "50.30",
  "provider": "DaisySMS"
}
```

### Todas las Transacciones (Admin)
```
GET /api/account/admin/transactions/
Authorization: Bearer <token_admin>

Query Params:
- user_id: Filtrar por usuario
- type: RENT, REFUND, MANUAL_CREDIT

Response (200 OK):
{
  "count": 100,
  "results": [ ... ]
}
```

---

## Codigos de Estado HTTP

- `200 OK` - Exitoso
- `201 Created` - Recurso creado exitosamente
- `400 Bad Request` - Datos invalidos o error de negocio
- `401 Unauthorized` - Sin autenticacion
- `403 Forbidden` - No tienes permisos
- `404 Not Found` - Recurso no existe
- `429 Too Many Requests` - Rate limit excedido
- `500 Internal Server Error` - Error del servidor
- `503 Service Unavailable` - DaisySMS API no disponible

---

## Rate Limiting

| Endpoint | Limite | Descripcion |
|----------|--------|-------------|
| GET /api/rentals/ | 120/hora | Polling cada 30 segundos |
| POST /api/rentals/ | 20/hora | Crear alquileres |
| POST /api/rentals/{id}/cancel/ | 60/hora | Cancelar alquileres |
| General (user) | 1000/hora | Otros endpoints autenticados |
| General (anon) | 100/hora | Endpoints sin autenticacion |

---

## Tipos de Transaccion

- `RENT` - Alquiler de numero (debito)
- `REFUND` - Reembolso (credito)
- `MANUAL_CREDIT` - Credito manual por admin (credito)
- `MANUAL_DEBIT` - Debito manual por admin (debito)

---

## Estados de Alquiler

| Estado | Descripcion |
|--------|-------------|
| `ACTIVE` | Esperando SMS |
| `SMS_RECEIVED` | SMS recibido exitosamente |
| `EXPIRED` | Expiro (con SMS recibido, sin reembolso) |
| `CANCELLED` | Cancelado por DaisySMS |
| `REFUNDED` | Reembolsado (expirado sin SMS o cancelado por usuario) |

---

## Codigos de Servicio Comunes

| Codigo | Servicio |
|--------|----------|
| wa | WhatsApp |
| go | Google |
| tg | Telegram |
| ig | Instagram |
| fb | Facebook |
| tw | Twitter/X |
| ds | Discord |
| vi | Viber |
| ap | Apple |
| ms | Microsoft |
| am | Amazon |
| nf | Netflix |
| sp | Spotify |
| ub | Uber |
| ti | TikTok |
| ai | OpenAI |

---

## Flujo Tipico de Uso (Simplificado)

```
1. Registrarse/Login -> Obtener token JWT
2. Ver balance -> GET /api/account/balance/
3. Ver servicios -> GET /api/services/?available=true
4. Alquilar numero -> POST /api/rentals/
5. Polling para SMS -> GET /api/rentals/ (cada 3-5 segundos)
   - El endpoint sincroniza con DaisySMS
   - Devuelve SMS cuando llega
   - Procesa reembolso si expira sin SMS
6. (Opcional) Cancelar -> POST /api/rentals/{id}/cancel/
```

### Diagrama de Flujo
```
Frontend                           Backend                         DaisySMS
   |                                  |                               |
   |-- POST /api/rentals/ ----------->|                               |
   |                                  |-- rent_number() ------------->|
   |                                  |<-- rental_id, phone ---------|
   |<-- rental created (ACTIVE) -----|                               |
   |                                  |                               |
   |-- GET /api/rentals/ ------------>|                               |
   |   (polling every 3-5s)           |-- get_sms_status() --------->|
   |                                  |<-- WAIT (no SMS yet) --------|
   |<-- rentals[] (ACTIVE) ----------|                               |
   |                                  |                               |
   |-- GET /api/rentals/ ------------>|                               |
   |                                  |-- get_sms_status() --------->|
   |                                  |<-- OK + code: 123456 --------|
   |                                  |   (save SMS to DB)           |
   |<-- rentals[] (SMS_RECEIVED) ----|                               |
   |                                  |                               |
   |   [USER USES THE CODE]           |                               |
   |                                  |                               |
   --- OR if expires without SMS ---  |                               |
   |                                  |                               |
   |-- GET /api/rentals/ ------------>|                               |
   |                                  |   (detect expired)           |
   |                                  |   (process refund)           |
   |                                  |-- cancel_rental() ---------->|
   |<-- rentals[] (REFUNDED) --------|                               |
   |   + refund_amount_cup            |                               |
   |   + new_balance_cup              |                               |
```

---

## Ejemplos con cURL

### Registro
```bash
curl -X POST http://localhost:8000/api/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password1": "testpass123",
    "password2": "testpass123"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

### Ver Balance
```bash
curl -X GET http://localhost:8000/api/account/balance/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Ver Servicios
```bash
curl -X GET "http://localhost:8000/api/services/?available=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Alquilar Numero
```bash
curl -X POST http://localhost:8000/api/rentals/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_code": "wa",
    "max_price_usd": 0.50
  }'
```

### Listar Alquileres (Polling)
```bash
curl -X GET http://localhost:8000/api/rentals/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Listar Solo Activos
```bash
curl -X GET "http://localhost:8000/api/rentals/?status=ACTIVE" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Cancelar Alquiler
```bash
curl -X POST http://localhost:8000/api/rentals/1/cancel/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Notas Importantes

1. **Tasa de cambio**: 1 USD = 4800 CUP (configurable por admin)
2. **Tiempo de alquiler**: ~15 minutos por numero
3. **Reembolso automatico**: Se procesa cuando el frontend hace polling y detecta expiracion sin SMS
4. **Cache de servicios**: Los servicios se cachean por 5 minutos
5. **Polling recomendado**: Cada 3-5 segundos para GET /api/rentals/
6. **Limite de alquileres**: 5 activos simultaneos por usuario
7. **Arquitectura sin Celery**: Todo el procesamiento ocurre durante las peticiones HTTP
8. **Rate limiting**: Ver tabla de limites por endpoint
