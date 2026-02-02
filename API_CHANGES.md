# API Changes Documentation

Este documento describe los cambios realizados en los endpoints de la API del sistema SMS Rental Platform.

---

## Resumen de Cambios

| Endpoint | Método | Cambios |
|----------|--------|---------|
| `/api/services/` | GET | Corregido parsing de respuesta, soporte multi-país |
| `/api/rentals/` | POST | Validación mejorada, mejor manejo de errores |
| `/api/rentals/` | GET | Sin cambios (polling mantenido) |

---

## 1. GET `/api/services/` - Lista de Servicios

### Problemas Corregidos
- **CRÍTICO**: Se reemplazó `eval()` por `json.loads()` para parsear la respuesta de DaisySMS
- **CRÍTICO**: Se corrigió el parsing de la estructura de datos de servicios
- Se agregó soporte para múltiples países

### Query Parameters (Sin cambios)

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `country` | string | No | Filtrar por código de país (ej: `187` para USA) |
| `service_code` | string | No | Filtrar por código de servicio (ej: `wa`, `go`) |
| `available` | string | No | Si es `true`, solo muestra servicios con números disponibles |

### Response Body (Mejorado)

```json
{
  "services": [
    {
      "service_code": "wa",
      "name": "WhatsApp",
      "price_usd": "0.2500",
      "price_cup": "1200.00",
      "available_numbers": 100,
      "supports_multiple_sms": false,
      "country": "187",
      "country_name": "USA"    // MEJORADO: Ahora incluye nombres para 100+ países
    }
  ],
  "exchange_rate": "4800.00",
  "total": 50
}
```

### Nuevos Códigos de País Soportados

Se agregaron 100+ códigos de país. Los más comunes:

| Código | País |
|--------|------|
| `187` | USA |
| `18` | UK |
| `36` | Canada |
| `40` | Germany |
| `33` | France |
| `34` | Spain |
| `39` | Italy |
| `0` | Russia |
| `85` | India |
| `50` | Brazil |
| `73` | Mexico |
| `81` | Japan |
| `82` | South Korea |

---

## 2. POST `/api/rentals/` - Crear Rental

### Request Body (Validaciones Mejoradas)

| Campo | Tipo | Requerido | Default | Descripción |
|-------|------|-----------|---------|-------------|
| `service_code` | string | **Sí** | - | Código del servicio (ej: `wa`, `go`, `tg`) |
| `max_price_usd` | decimal | No | null | Precio máximo en USD |
| `country` | string | No | `"187"` | Código del país. **MEJORADO**: Ahora valida que sea un código válido |
| `areas` | string | No | null | Códigos de área separados por coma (ej: `212,718`). **MEJORADO**: Validación de formato |
| `carriers` | string | No | null | Carriers separados por coma. **MEJORADO**: Valida que sean `tmo`, `vz`, o `att` |
| `number` | string | No | null | Número específico. **MEJORADO**: Valida longitud (10-15 dígitos) |

### Ejemplo de Request

```json
{
  "service_code": "wa",
  "max_price_usd": "0.50",
  "country": "187",
  "areas": "212,718",
  "carriers": "tmo,vz"
}
```

### Response Body (Sin cambios estructurales)

```json
{
  "id": 1,
  "daisy_rental_id": 123456,
  "phone": "+12125551234",
  "service_code": "wa",
  "service_name": "WhatsApp",
  "status": "ACTIVE",
  "status_display": "Activo - Esperando SMS",
  "price_usd": "0.2500",
  "price_cup": "1200.00",
  "rented_at": "2026-02-01T10:00:00Z",
  "expires_at": "2026-02-01T10:15:00Z",
  "remaining_time_seconds": 900,
  "has_sms": false,
  "sms": [],
  "refunded": false,
  "new_balance_cup": "3600.00",
  "requested_areas": "212,718",
  "price_markup_note": "Área específica: +20% al precio"
}
```

### Nuevos Errores de Validación

#### Error: País inválido
```json
{
  "country": [
    "Codigo de pais invalido: 999. Codigos comunes: 187=USA, 18=UK, 36=Canada, 40=Germany, 0=Russia, 85=India"
  ]
}
```

#### Error: Área inválida
```json
{
  "areas": [
    "Formato de area invalido: abc. Use numeros separados por comas (ej: 212,718)"
  ]
}
```

#### Error: Carrier inválido
```json
{
  "carriers": [
    "Carrier invalido: xyz. Carriers validos: tmo (T-Mobile), vz (Verizon), att (AT&T)"
  ]
}
```

#### Error: Número inválido
```json
{
  "number": [
    "Numero invalido: 123. Debe tener entre 10 y 15 digitos"
  ]
}
```

#### Error: Servicio no disponible en país (NUEVO)
```json
{
  "error": "Servicio wa no disponible en el pais 40",
  "available_countries": ["187", "18", "36"],
  "hint": "Use GET /api/services/?service_code=wa para ver paises disponibles"
}
```

---

## 3. GET `/api/rentals/` - Lista de Rentals (Polling)

### Sin cambios

Este endpoint se mantiene exactamente igual. Sigue siendo el endpoint para polling que sincroniza el estado de los rentals con DaisySMS.

### Query Parameters

| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|-------------|
| `status` | string | No | `ALL` | Filtrar por estado: `ACTIVE`, `SMS_RECEIVED`, `REFUNDED`, `CANCELLED`, `ALL` |
| `limit` | int | No | 50 | Número de resultados por página |
| `offset` | int | No | 0 | Offset para paginación |

### Response Body (Sin cambios)

```json
{
  "rentals": [...],
  "balance_cup": "4800.00",
  "total": 10,
  "limit": 50,
  "offset": 0
}
```

---

## 4. POST `/api/rentals/<id>/cancel/` - Cancelar Rental

### Sin cambios

Este endpoint se mantiene exactamente igual.

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `apps/services/daisy_client.py` | Reemplazado `eval()` → `json.loads()`, expandido `COUNTRY_NAMES` a 100+ países, agregado parámetro `country` a `rent_number()` |
| `apps/services/daisy_client_mock.py` | Agregado soporte multi-país en mock, datos de prueba para 8 países |
| `apps/services/serializers.py` | Expandido `COUNTRY_NAMES` en `ServiceSerializer` |
| `apps/rentals/serializers.py` | Agregadas validaciones para `country`, `areas`, `carriers`, `number` |
| `apps/rentals/views.py` | Mejorado manejo de errores cuando servicio no está disponible en país |

---

## Códigos de País Completos

```
'0': Russia          '40': Germany        '73': Mexico
'1': Ukraine         '41': Pakistan       '74': Chile
'2': Kazakhstan      '43': Ireland        '75': Uganda
'3': China           '44': Portugal       '76': Uzbekistan
'4': Philippines     '46': Azerbaijan     '77': Georgia
'5': Myanmar         '47': Bangladesh     '78': Albania
'6': Indonesia       '49': Austria        '79': Luxembourg
'7': Malaysia        '50': Brazil         '80': Switzerland
'8': Kenya           '51': Romania        '81': Japan
'9': Tanzania        '52': Belgium        '82': South Korea
'10': Vietnam        '53': New Zealand    '83': Taiwan
'11': Kyrgyzstan     '54': Australia      '84': Thailand
'12': USA (Virtual)  '55': Finland        '85': India
'14': Egypt          '56': Hungary        '86': Singapore
'15': Israel         '57': Lithuania      '87': UAE
'16': Hong Kong      '58': Latvia         '88': Saudi Arabia
'17': Poland         '59': Moldova        '89': Tajikistan
'18': UK             '60': Cambodia       '90': Bolivia
'19': Madagascar     '61': Ghana          '91': Costa Rica
'20': DR Congo       '62': Colombia       '92': Ecuador
'21': Nigeria        '63': Peru           '93': Paraguay
'22': Macau          '64': Greece         '94': Uruguay
'23': Estonia        '65': Denmark        '95': Venezuela
'24': Sri Lanka      '66': Norway         '96': Panama
'25': Ivory Coast    '67': Slovakia       '97': Dominican Republic
'26': Gambia         '68': Slovenia       '98': Guatemala
'27': Serbia         '69': Bulgaria       '99': El Salvador
'28': Morocco        '70': Croatia        '100': Honduras
'29': Cameroon       '71': Nepal          '101': Nicaragua
'30': South Africa   '72': Argentina      '102': Puerto Rico
'31': Sweden         '117': Zambia
'32': Netherlands    '129': Zimbabwe
'33': France         '187': USA
'34': Spain
'36': Canada
'37': Turkey
'38': Czech Republic
'39': Italy
```

---

## Notas Importantes

1. **DaisySMS es principalmente un servicio de USA**: Aunque el sistema ahora soporta múltiples países, DaisySMS se enfoca en números de USA. Los otros países pueden tener disponibilidad limitada.

2. **El polling se mantiene**: El endpoint `GET /api/rentals/` sigue usando el mismo mecanismo de polling. El frontend debe seguir llamando a este endpoint periódicamente para obtener actualizaciones de SMS.

3. **Cache de servicios**: Los servicios se cachean por 5 minutos para reducir llamadas a la API de DaisySMS.

4. **Markup de 20%**: Usar `areas`, `carriers`, o `number` agrega un 20% al precio del servicio.
