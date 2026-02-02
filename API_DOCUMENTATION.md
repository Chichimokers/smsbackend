# SMS Rental Platform - API Documentation

**Base URL:** `https://inventory.cloudns.be`

**Autenticación:** JWT Bearer Token  
Header: `Authorization: Bearer <access_token>`

---

## Tabla de Contenidos

1. [Autenticación](#1-autenticación)
2. [Cuenta de Usuario](#2-cuenta-de-usuario)
3. [Servicios](#3-servicios)
4. [Rentals (Alquileres)](#4-rentals-alquileres)
5. [Códigos de Error](#5-códigos-de-error)
6. [Flujo Típico del Frontend](#6-flujo-típico-del-frontend)

---

## 1. Autenticación

### 1.1 Registro de Usuario

**Endpoint:** `POST /api/users/register/`  
**Auth:** No requerida

**Request Body:**
```json
{
  "email": "usuario@ejemplo.com",
  "password1": "mipassword123",
  "password2": "mipassword123",
  "first_name": "Juan",
  "last_name": "Pérez"
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| email | string | Sí | Email único del usuario |
| password1 | string | Sí | Contraseña (mín 8 caracteres) |
| password2 | string | Sí | Confirmación de contraseña |
| first_name | string | No | Nombre |
| last_name | string | No | Apellido |

**Response (201 Created):**
```json
{
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "full_name": "Juan Pérez",
    "date_joined": "2026-02-01T12:00:00Z",
    "is_staff": false
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  },
  "message": "Registro exitoso"
}
```

**Errores posibles:**
```json
// Email duplicado
{
  "email": ["Ya existe un usuario con este email."]
}

// Contraseñas no coinciden
{
  "password2": ["Las contraseñas no coinciden."]
}
```

---

### 1.2 Login

**Endpoint:** `POST /api/users/login/`  
**Auth:** No requerida

**Request Body:**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "mipassword123"
}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "full_name": "Juan Pérez",
    "date_joined": "2026-02-01T12:00:00Z",
    "is_staff": false
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  },
  "message": "Login exitoso"
}
```

**Errores posibles:**
```json
{
  "non_field_errors": ["Credenciales inválidas."]
}
```

---

### 1.3 Logout

**Endpoint:** `POST /api/users/logout/`  
**Auth:** Requerida

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
  "message": "Logout exitoso"
}
```

---

### 1.4 Refresh Token

**Endpoint:** `POST /api/users/token/refresh/`  
**Auth:** No requerida

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### 1.5 Obtener Perfil

**Endpoint:** `GET /api/users/profile/`  
**Auth:** Requerida

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "usuario@ejemplo.com",
  "first_name": "Juan",
  "last_name": "Pérez",
  "full_name": "Juan Pérez",
  "date_joined": "2026-02-01T12:00:00Z",
  "is_staff": false
}
```

---

### 1.6 Actualizar Perfil

**Endpoint:** `PATCH /api/users/profile/`  
**Auth:** Requerida

**Request Body:**
```json
{
  "first_name": "Juan Carlos",
  "last_name": "Pérez González"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "usuario@ejemplo.com",
  "first_name": "Juan Carlos",
  "last_name": "Pérez González",
  "full_name": "Juan Carlos Pérez González",
  "date_joined": "2026-02-01T12:00:00Z",
  "is_staff": false
}
```

---

## 2. Cuenta de Usuario

### 2.1 Obtener Balance

**Endpoint:** `GET /api/account/balance/`  
**Auth:** Requerida

**Response (200 OK):**
```json
{
  "balance_cup": "50000.00",
  "balance_usd": "10.42",
  "exchange_rate": "4800.00",
  "currency": "CUP"
}
```

| Campo | Descripción |
|-------|-------------|
| balance_cup | Saldo en pesos cubanos (CUP) |
| balance_usd | Saldo equivalente en USD |
| exchange_rate | Tasa de cambio actual (CUP por 1 USD) |
| currency | Moneda principal de la cuenta |

---

### 2.2 Historial de Transacciones

**Endpoint:** `GET /api/account/transactions/`  
**Auth:** Requerida

**Query Params:**
| Param | Descripción |
|-------|-------------|
| page | Número de página (default: 1) |

**Response (200 OK):**
```json
{
  "count": 25,
  "next": "https://inventory.cloudns.be/api/account/transactions/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "type": "RENTAL",
      "type_display": "Alquiler",
      "amount_cup": "-4800.00",
      "amount_usd": "-1.00",
      "balance_after_cup": "45200.00",
      "description": "Alquiler Telegram: +1 (555) 123-4567",
      "created_at": "2026-02-01T12:00:00Z",
      "rental_id": 1
    },
    {
      "id": 2,
      "type": "REFUND",
      "type_display": "Reembolso",
      "amount_cup": "4800.00",
      "amount_usd": "1.00",
      "balance_after_cup": "50000.00",
      "description": "Reembolso automático: +1 (555) 123-4567 (expirado sin SMS)",
      "created_at": "2026-02-01T12:15:00Z",
      "rental_id": 1
    },
    {
      "id": 3,
      "type": "CREDIT",
      "type_display": "Crédito",
      "amount_cup": "50000.00",
      "amount_usd": "10.42",
      "balance_after_cup": "50000.00",
      "description": "Recarga de saldo",
      "created_at": "2026-02-01T11:00:00Z",
      "rental_id": null
    }
  ]
}
```

**Tipos de Transacción:**
| Tipo | Descripción |
|------|-------------|
| CREDIT | Crédito/Recarga de saldo |
| RENTAL | Cobro por alquiler de número |
| REFUND | Reembolso (cancelación o expiración sin SMS) |

---

### 2.3 Tasa de Cambio

**Endpoint:** `GET /api/account/exchange-rate/`  
**Auth:** No requerida

**Response (200 OK):**
```json
{
  "rate_cup_per_usd": "4800.00",
  "description": "1 USD = 4800.00 CUP",
  "last_updated": "2026-02-01T10:00:00Z"
}
```

---

## 3. Servicios

### 3.1 Listar Servicios Disponibles

**Endpoint:** `GET /api/services/`  
**Auth:** Requerida

**Query Params:**
| Param | Descripción | Ejemplo |
|-------|-------------|---------|
| country | Filtrar por código de país | 187 (USA) |
| service_code | Filtrar por código de servicio | tg, wa, go |
| available | Solo servicios con números disponibles | true |

**Response (200 OK):**
```json
{
  "services": [
    {
      "service_code": "tg",
      "name": "Telegram",
      "price_usd": "0.50",
      "price_cup": "2400.00",
      "available_numbers": 150,
      "country": "187",
      "country_name": "USA"
    },
    {
      "service_code": "wa",
      "name": "WhatsApp",
      "price_usd": "3.50",
      "price_cup": "16800.00",
      "available_numbers": 45,
      "country": "187",
      "country_name": "USA"
    },
    {
      "service_code": "go",
      "name": "Google/Gmail",
      "price_usd": "1.00",
      "price_cup": "4800.00",
      "available_numbers": 200,
      "country": "187",
      "country_name": "USA"
    },
    {
      "service_code": "ig",
      "name": "Instagram",
      "price_usd": "1.20",
      "price_cup": "5760.00",
      "available_numbers": 80,
      "country": "187",
      "country_name": "USA"
    },
    {
      "service_code": "fb",
      "name": "Facebook",
      "price_usd": "0.75",
      "price_cup": "3600.00",
      "available_numbers": 120,
      "country": "187",
      "country_name": "USA"
    }
  ],
  "exchange_rate": "4800.00",
  "total": 5
}
```

**Códigos de Servicio Comunes:**
| Código | Servicio |
|--------|----------|
| tg | Telegram |
| wa | WhatsApp |
| go | Google/Gmail |
| ig | Instagram |
| fb | Facebook |
| tw | Twitter/X |
| dc | Discord |
| tk | TikTok |
| am | Amazon |
| nf | Netflix |

---

## 4. Rentals (Alquileres)

### 4.1 Crear Rental (Alquilar Número)

**Endpoint:** `POST /api/rentals/`  
**Auth:** Requerida

**Request Body (básico):**
```json
{
  "service_code": "tg",
  "country": "187",
  "max_price_usd": 2.00
}
```

**Request Body (con parámetros opcionales):**
```json
{
  "service_code": "tg",
  "country": "187",
  "max_price_usd": 2.00,
  "areas": "212,718",
  "carriers": "tmo,vz",
  "number": "12125551234"
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| service_code | string | Sí | Código del servicio (tg, wa, go, etc.) |
| country | string | No | Código de país (default: 187 = USA) |
| max_price_usd | decimal | No | Precio máximo a pagar en USD |
| areas | string | No | Códigos de área (ej: 212,718) - **Añade 20% al precio** |
| carriers | string | No | Operadores: tmo, vz, att (ej: tmo,vz) - **Añade 20% al precio** |
| number | string | No | Número específico (ej: 12125551234) - **Añade 20% al precio** |

**Notas sobre parámetros opcionales:**
- `areas`: Especifica qué códigos de área quieres (ej: 212 = Nueva York, 718 = Brooklyn)
- `carriers`: Especifica qué operadora móvil (TMO = T-Mobile, VZ = Verizon, ATT = AT&T)
- `number`: Solicita un número específico (si está disponible)
- **Importante:** Estos parámetros añaden un **20% extra al precio** según la API de DaisySMS
- Los parámetros son opcionales y pueden combinarse

**Response (201 Created):**
```json
{
  "id": 1,
  "daisy_rental_id": "123456789",
  "phone": "+1 (555) 123-4567",
  "service_code": "tg",
  "service_name": "Telegram",
  "status": "ACTIVE",
  "status_display": "Activo",
  "price_usd": "0.50",
  "price_cup": "2400.00",
  "rented_at": "2026-02-01T12:00:00Z",
  "expires_at": "2026-02-01T12:15:00Z",
  "remaining_time_seconds": 900,
  "has_sms": false,
  "sms": [],
  "refunded": false,
  "new_balance_cup": "47600.00",
  "requested_areas": "212,718",
  "price_markup_note": "Área específica: +20% al precio"
}
```

**Campos adicionales en response (cuando aplica):**
- `requested_areas`: Muestra los códigos de área solicitados
- `requested_carrier`: Muestra el operador solicitado
- `requested_number`: Muestra el número solicitado
- `price_markup_note`: Nota explicando el markup del 20%

**Errores posibles:**

```json
// Máximo de rentals activos alcanzado
{
  "error": "Máximo 5 alquileres activos permitidos",
  "active_rentals": 5,
  "message": "Espera a que expiren o cancela algunos para crear nuevos"
}

// Saldo insuficiente
{
  "error": "Saldo insuficiente",
  "required_cup": "2400.00",
  "available_cup": "1000.00"
}

// No hay números disponibles
{
  "error": "No hay números disponibles para tg"
}

// Servicio no encontrado
{
  "error": "Servicio tg no disponible"
}

// Precio excede máximo especificado
{
  "error": "El precio excede el máximo especificado"
}
```

**Ejemplos de uso:**

Alquilar Telegram con área code específica (Nueva York):
```bash
curl -X POST https://inventory.cloudns.be/api/rentals/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_code": "tg",
    "areas": "212"
  }'
```

Alquilar WhatsApp de T-Mobile:
```bash
curl -X POST https://inventory.cloudns.be/api/rentals/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_code": "wa",
    "carriers": "tmo"
  }'
```

Alquilar Instagram de un número específico:
```bash
curl -X POST https://inventory.cloudns.be/api/rentals/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_code": "ig",
    "number": "12125551234",
    "max_price_usd": 1.00
  }'
```

---

### 4.2 Listar Rentals (con Polling/Sync)

**Endpoint:** `GET /api/rentals/`  
**Auth:** Requerida

Este endpoint es **crítico** para el frontend. Debe ser llamado cada 3-5 segundos para:
- Verificar si llegó SMS
- Actualizar tiempo restante
- Procesar reembolsos automáticos de rentals expirados

**Query Params:**
| Param | Descripción | Default |
|-------|-------------|---------|
| status | Filtrar por estado | ALL |
| limit | Cantidad de resultados | 50 |
| offset | Paginación | 0 |

**Valores de status:**
- `ACTIVE` - Solo rentals activos esperando SMS
- `SMS_RECEIVED` - Solo rentals que recibieron SMS
- `REFUNDED` - Solo rentals reembolsados
- `CANCELLED` - Solo rentals cancelados
- `ALL` - Todos los rentals

**Response (200 OK):**
```json
{
  "rentals": [
    {
      "id": 1,
      "daisy_rental_id": "123456789",
      "phone": "+1 (555) 123-4567",
      "service_code": "tg",
      "service_name": "Telegram",
      "status": "ACTIVE",
      "status_display": "Activo",
      "price_cup": "2400.00",
      "price_usd": "0.50",
      "rented_at": "2026-02-01T12:00:00Z",
      "expires_at": "2026-02-01T12:15:00Z",
      "remaining_time_seconds": 540,
      "has_sms": false,
      "sms": [],
      "refunded": false
    },
    {
      "id": 2,
      "daisy_rental_id": "123456790",
      "phone": "+1 (555) 987-6543",
      "service_code": "wa",
      "service_name": "WhatsApp",
      "status": "SMS_RECEIVED",
      "status_display": "SMS Recibido",
      "price_cup": "16800.00",
      "price_usd": "3.50",
      "rented_at": "2026-02-01T11:50:00Z",
      "expires_at": "2026-02-01T12:05:00Z",
      "remaining_time_seconds": 0,
      "has_sms": true,
      "sms": [
        {
          "id": 1,
          "code": "123456",
          "full_text": "Your WhatsApp code is 123456. Do not share.",
          "received_at": "2026-02-01T11:52:30Z"
        }
      ],
      "refunded": false
    },
    {
      "id": 3,
      "daisy_rental_id": "123456788",
      "phone": "+1 (555) 111-2222",
      "service_code": "go",
      "service_name": "Google/Gmail",
      "status": "REFUNDED",
      "status_display": "Reembolsado",
      "price_cup": "4800.00",
      "price_usd": "1.00",
      "rented_at": "2026-02-01T11:30:00Z",
      "expires_at": "2026-02-01T11:45:00Z",
      "remaining_time_seconds": 0,
      "has_sms": false,
      "sms": [],
      "refunded": true,
      "refund_amount_cup": "4800.00"
    }
  ],
  "balance_cup": "47600.00",
  "total": 3,
  "limit": 50,
  "offset": 0
}
```

**Estados de Rental:**
| Estado | Descripción | Reembolsable |
|--------|-------------|--------------|
| ACTIVE | Esperando SMS, timer corriendo | Sí (manual) |
| SMS_RECEIVED | SMS llegó exitosamente | No |
| REFUNDED | Reembolsado (cancelado o expirado sin SMS) | Ya reembolsado |
| CANCELLED | Cancelado por el proveedor | No |
| EXPIRED | Expiró pero tenía SMS (sin reembolso) | No |

**Campos importantes para el frontend:**
| Campo | Uso |
|-------|-----|
| remaining_time_seconds | Mostrar countdown timer |
| has_sms | Verificar si llegó SMS |
| sms[0].code | El código de verificación a mostrar |
| status | Determinar estado visual del rental |
| refunded | Mostrar badge de reembolso |

---

### 4.3 Cancelar Rental

**Endpoint:** `POST /api/rentals/{id}/cancel/`  
**Auth:** Requerida

**Condiciones:**
- El rental debe estar en estado `ACTIVE`
- No debe haber recibido SMS

**Request Body:** Ninguno (empty)

**Response (200 OK):**
```json
{
  "rental_id": 1,
  "status": "REFUNDED",
  "status_display": "Reembolsado",
  "refunded": true,
  "refund_amount_cup": "2400.00",
  "new_balance_cup": "50000.00",
  "message": "Alquiler cancelado y reembolsado exitosamente"
}
```

**Errores posibles:**
```json
// Rental no está activo
{
  "error": "Este alquiler no puede ser cancelado",
  "current_status": "SMS_RECEIVED",
  "status_display": "SMS Recibido"
}

// Ya tiene SMS
{
  "error": "No se puede cancelar un alquiler con SMS recibido"
}
```

---

## 5. Códigos de Error

### HTTP Status Codes

| Código | Descripción |
|--------|-------------|
| 200 | OK - Solicitud exitosa |
| 201 | Created - Recurso creado |
| 400 | Bad Request - Error de validación |
| 401 | Unauthorized - Token inválido o expirado |
| 403 | Forbidden - Sin permisos |
| 404 | Not Found - Recurso no encontrado |
| 429 | Too Many Requests - Rate limit excedido |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Error con DaisySMS |

### Estructura de Error

```json
{
  "error": "Mensaje de error principal",
  "detail": "Detalles adicionales (opcional)"
}
```

O para errores de validación:
```json
{
  "field_name": ["Error 1", "Error 2"],
  "non_field_errors": ["Error general"]
}
```

---

## 6. Flujo Típico del Frontend

### 6.1 Registro/Login
```
1. Usuario ingresa datos → POST /api/users/register/ o /login/
2. Guardar tokens en localStorage/cookies
3. Usar access token en header: Authorization: Bearer <token>
4. Si access token expira → POST /api/users/token/refresh/
```

### 6.2 Ver Servicios y Crear Rental
```
1. Cargar servicios → GET /api/services/
2. Mostrar lista con precios en CUP
3. Usuario selecciona servicio → POST /api/rentals/
4. Mostrar número de teléfono y timer countdown
```

### 6.3 Polling de SMS (CRÍTICO)
```javascript
// Cada 3-5 segundos mientras haya rentals ACTIVE
const pollRentals = async () => {
  const response = await fetch('/api/rentals/?status=ACTIVE', {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  const data = await response.json();
  
  for (const rental of data.rentals) {
    // Actualizar timer
    updateTimer(rental.id, rental.remaining_time_seconds);
    
    // Verificar si llegó SMS
    if (rental.has_sms) {
      showSMSCode(rental.id, rental.sms[0].code);
      playNotificationSound();
    }
    
    // Verificar si fue reembolsado automáticamente
    if (rental.refunded) {
      showRefundNotification(rental.refund_amount_cup);
    }
  }
  
  // Actualizar balance mostrado
  updateBalanceDisplay(data.balance_cup);
};

// Iniciar polling
setInterval(pollRentals, 4000);
```

### 6.4 Cancelar Rental
```
1. Usuario hace click en "Cancelar"
2. Confirmar acción
3. POST /api/rentals/{id}/cancel/
4. Mostrar nuevo balance y mensaje de éxito
```

---

## 7. Ejemplo de Implementación Frontend

### Headers Requeridos
```javascript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${accessToken}`
};
```

### Manejo de Token Expirado
```javascript
const fetchWithAuth = async (url, options = {}) => {
  let response = await fetch(url, {
    ...options,
    headers: { ...headers, ...options.headers }
  });
  
  if (response.status === 401) {
    // Token expirado, intentar refresh
    const refreshResponse = await fetch('/api/users/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken })
    });
    
    if (refreshResponse.ok) {
      const tokens = await refreshResponse.json();
      // Guardar nuevos tokens
      localStorage.setItem('access', tokens.access);
      localStorage.setItem('refresh', tokens.refresh);
      
      // Reintentar request original
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${tokens.access}`
        }
      });
    } else {
      // Refresh token inválido, redirigir a login
      window.location.href = '/login';
    }
  }
  
  return response;
};
```

---

## 8. Rate Limits

| Endpoint | Límite |
|----------|--------|
| Anónimo | 100/hora |
| Autenticado | 1000/hora |
| POST /api/rentals/ | 20/hora |
| GET /api/rentals/ | 120/hora |
| POST /api/rentals/{id}/cancel/ | 60/hora |

---

## 9. Notas Importantes

1. **Tiempo de expiración:** Los rentals expiran en 15 minutos
2. **Reembolso automático:** Si expira sin SMS, se reembolsa automáticamente
3. **Máximo activos:** 5 rentals activos por usuario
4. **Polling:** Frontend debe hacer polling cada 3-5 segundos
5. **Tokens JWT:** Access token dura 1 día, Refresh token 7 días
