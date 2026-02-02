# Actualización DaisySMS API Integration - Parámetros Opcionales

**Fecha:** 1 Febrero 2026  
**Versión:** 1.1.0  
**Objetivo:** Añadir soporte para parámetros opcionales (areas, carriers, número específico) al alquilar números en DaisySMS.

---

## 📋 Resumen de Cambios

Se implementó soporte completo para los parámetros opcionales del API de DaisySMS según la documentación oficial:

- **areas**: Especificar códigos de área (ej: 212,718) - +20% al precio
- **carriers**: Especificar operador (ej: tmo,vz,att) - +20% al precio  
- **number**: Especificar número exacto (ej: 11112223344) - +20% al precio

Todos estos parámetros son **opcionales** y **aumentan el precio en un 20%** cuando se utilizan.

---

## 🔧 Archivos Modificados

### 1. **`apps/services/daisy_client.py`**

#### Método actualizado: `rent_number()`

**Antes:**
```python
def rent_number(
    self,
    service_code: str,
    max_price_usd: Optional[Decimal] = None
) -> RentalResult:
```

**Después:**
```python
def rent_number(
    self,
    service_code: str,
    max_price_usd: Optional[Decimal] = None,
    areas: Optional[str] = None,
    carriers: Optional[str] = None,
    number: Optional[str] = None
) -> RentalResult:
```

**Cambios:**
- Se añadieron 3 parámetros opcionales: `areas`, `carriers`, `number`
- Los parámetros se pasan directamente al API de DaisySMS
- La estructura de parámetros ahora es:
  ```python
  params = {
      'action': 'getNumber',
      'service': service_code,
      'max_price': str(max_price_usd),  # if provided
      'areas': areas,                    # NEW
      'carriers': carriers,              # NEW
      'number': number                   # NEW
  }
  ```

**Líneas modificadas:** 260-295

---

### 2. **`apps/rentals/serializers.py`**

#### Serializer actualizado: `RentNumberSerializer`

**Cambios:** Se añadieron 3 nuevos campos opcionales

```python
areas = serializers.CharField(
    max_length=100,
    required=False,
    allow_blank=True,
    help_text='Area codes (ej: 212,718) - Añade 20% al precio'
)

carriers = serializers.CharField(
    max_length=50,
    required=False,
    allow_blank=True,
    help_text='Carriers (ej: tmo,vz,att) - Añade 20% al precio'
)

number = serializers.CharField(
    max_length=20,
    required=False,
    allow_blank=True,
    help_text='Numero especifico (ej: 11112223344) - Añade 20% al precio'
)
```

**Líneas modificadas:** 22-44

---

### 3. **`apps/rentals/views.py`**

#### Método actualizado: `RentalView.post()`

**Cambios principales:**

1. **Extracción de parámetros opcionales:**
   ```python
   areas = serializer.validated_data.get('areas') or None
   carriers = serializer.validated_data.get('carriers') or None
   number = serializer.validated_data.get('number') or None
   ```

2. **Paso de parámetros al cliente:**
   ```python
   rental_result = client.rent_number(
       service_code=service_code,
       max_price_usd=max_price_usd,
       areas=areas,        # NEW
       carriers=carriers,  # NEW
       number=number       # NEW
   )
   ```

3. **Respuesta mejorada:** Ahora incluye información sobre los parámetros solicitados
   ```python
   if areas:
       response_data['requested_areas'] = areas
       response_data['price_markup_note'] = 'Área específica: +20% al precio'
   if carriers:
       response_data['requested_carrier'] = carriers
       response_data['price_markup_note'] = 'Carrier específico: +20% al precio'
   if number:
       response_data['requested_number'] = number
       response_data['price_markup_note'] = 'Número específico: +20% al precio'
   ```

**Líneas modificadas:** 220-340

---

### 4. **`apps/services/daisy_client_mock.py`**

#### Método actualizado: `rent_number()`

**Cambios:** El mock ahora soporta los mismos parámetros que el real

```python
def rent_number(
    self,
    service_code: str,
    max_price_usd: Optional[Decimal] = None,
    areas: Optional[str] = None,
    carriers: Optional[str] = None,
    number: Optional[str] = None
) -> RentalResult:
```

**Lógica de markup del 20%:**
```python
# Apply 20% markup if special options requested
if areas or carriers or number:
    price = price * Decimal('1.20')
```

**Líneas modificadas:** 199-280

---

## 🔌 Endpoints Modificados

### `POST /api/rentals/` - Alquilar número

**Request Body Anterior:**
```json
{
    "service_code": "wa",
    "max_price_usd": 0.50,
    "country": "187"
}
```

**Request Body Nuevo (Soporta opcionales):**
```json
{
    "service_code": "wa",
    "max_price_usd": 0.50,
    "country": "187",
    "areas": "212,718",
    "carriers": "tmo",
    "number": "11112223344"
}
```

**Parámetros:**
- `service_code` (string, requerido): Código del servicio (wa, go, tg, etc)
- `max_price_usd` (decimal, opcional): Precio máximo en USD
- `country` (string, opcional): Código de país (default: 187 para USA)
- `areas` (string, opcional): Códigos de área separados por comas (ej: 212,718)
  - **Nota:** Añade 20% al precio
- `carriers` (string, opcional): Operadores (tmo, vz, att) separados por comas
  - **Nota:** Añade 20% al precio
- `number` (string, opcional): Número de teléfono específico (ej: 11112223344)
  - **Nota:** Añade 20% al precio

**Response (POST /api/rentals/)**

```json
{
    "id": 123,
    "daisy_rental_id": 999999,
    "phone": "+11112223344",
    "service_code": "wa",
    "service_name": "WhatsApp",
    "status": "ACTIVE",
    "status_display": "Activo - Esperando SMS",
    "price_usd": "0.30",
    "price_cup": "1440.00",
    "rented_at": "2026-02-01T22:30:45.123456Z",
    "expires_at": "2026-02-01T22:45:45.123456Z",
    "remaining_time_seconds": 900,
    "has_sms": false,
    "sms": [],
    "refunded": false,
    "new_balance_cup": "4358.60",
    "requested_areas": "212,718",
    "price_markup_note": "Área específica: +20% al precio"
}
```

**Campos nuevos en response:**
- `requested_areas`: Muestra los area codes solicitados (si aplica)
- `requested_carrier`: Muestra el carrier solicitado (si aplica)
- `requested_number`: Muestra el número solicitado (si aplica)
- `price_markup_note`: Nota explicando el markup del 20% (si aplica)

---

## 📊 Ejemplos de Uso

### Ejemplo 1: Alquilar con área específica

```bash
curl -X POST http://localhost:8000/api/rentals/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_code": "wa",
    "max_price_usd": 0.50,
    "areas": "212,718"
  }'
```

**Resultado:**
- Se alquilará un número de WhatsApp
- Será de los area codes 212 o 718
- El precio será **+20% más caro** de lo normal
- Ejemplo: Si WhatsApp normalmente cuesta $0.25, con área específica costará $0.30

### Ejemplo 2: Alquilar con carrier específico

```bash
curl -X POST http://localhost:8000/api/rentals/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_code": "go",
    "max_price_usd": 0.50,
    "carriers": "tmo,vz"
  }'
```

**Resultado:**
- Se alquilará un número de Google
- Será de T-Mobile o Verizon
- El precio será **+20% más caro**

### Ejemplo 3: Alquilar número específico

```bash
curl -X POST http://localhost:8000/api/rentals/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_code": "tg",
    "max_price_usd": 0.50,
    "number": "12125551234"
  }'
```

**Resultado:**
- Se intentará alquilar ese número específico para Telegram
- Si no está disponible, DaisySMS devuelve error `NO_NUMBERS`
- Si está disponible, el precio será **+20% más caro**

### Ejemplo 4: Combinar múltiples parámetros

```bash
curl -X POST http://localhost:8000/api/rentals/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_code": "ig",
    "max_price_usd": 1.00,
    "areas": "212",
    "carriers": "tmo"
  }'
```

**Resultado:**
- Area code 212 + T-Mobile = **+20%** markup
- Si el precio base de Instagram es $0.35, costará $0.42

---

## ⚠️ Notas Importantes

### Markup del 20%

Según la documentación de DaisySMS, los siguientes parámetros **SIEMPRE añaden un 20% extra al precio**:

- `areas` - Especificar códigos de área
- `carriers` - Especificar operador (TMO/VZ/ATT)
- `number` - Especificar número exacto

Si se combinan múltiples parámetros, **el markup se aplica UNA SOLA VEZ**, no se acumula.

**Ejemplo:**
- Precio base: $0.50
- Con area + carrier: $0.50 × 1.20 = $0.60 (no $0.72)

### Max Price Header

Es **altamente recomendado** siempre incluir `max_price_usd` para:
- Evitar sorpresas si DaisySMS sube precios
- Tener control sobre cuánto estás pagando
- Prevenir gastos inesperados

### Límite de Rentals Activos

- DaisySMS permite **máximo 20 rentals activos simultáneamente** por cuenta
- El sistema tiene un límite de **5 por usuario** (configurable en `MAX_ACTIVE_RENTALS`)
- Una vez recibas el SMS o canceles, puedes alquilar otro

### Validación de Parámetros

Los parámetros opcionales se validan en el serializer pero DaisySMS también los valida:
- `areas`: Formato "212,718" (códigos separados por comas)
- `carriers`: Solo "tmo", "vz", "att"
- `number`: Formato "+1XXXXXXXXXX" o "1XXXXXXXXXX"

---

## 🧪 Testing

Para probar sin gastar dinero real, usa `MOCK_DAISY_SMS=true` en `.env`.

El mock ahora también soporta los nuevos parámetros:

```python
# Test con mock
from apps.services.daisy_client import get_daisy_client

client = get_daisy_client()

# Alquilar con area codes
result = client.rent_number(
    service_code='wa',
    areas='212,718'
)
# El mock aplicará el 20% de markup automáticamente
```

---

## 🔄 Migraciones Requeridas

**Ninguna.** No se modificaron modelos de base de datos.

Se guardó información adicional en el response pero en campos informacionales solamente.

---

## 📝 Cambios en DocumentaciónAPI

El archivo `API_DOCUMENTATION.md` debe actualizarse para reflejar:
- Los nuevos parámetros opcionales en POST /api/rentals/
- Ejemplos de uso con areas, carriers, number
- Nota sobre el markup del 20%

---

## ✅ Checklist de Testing

- [ ] Alquilar número sin parámetros opcionales (debe funcionar igual que antes)
- [ ] Alquilar con `areas` solamente
- [ ] Alquilar con `carriers` solamente
- [ ] Alquilar con `number` solamente
- [ ] Alquilar combinando múltiples parámetros
- [ ] Verificar que el precio se incrementa en 20%
- [ ] Verificar que se devuelven los campos nuevos en la response
- [ ] Probar con max_price que debería falla (MAX_PRICE_EXCEEDED)
- [ ] Probar sin balance suficiente (NO_MONEY)
- [ ] Verificar logs de DaisySMS para cada request

---

## 🚀 Próximos Pasos

1. **Actualizar API_DOCUMENTATION.md** con los nuevos parámetros
2. **Validar con API real** de DaisySMS
3. **Implementar FASE 2** (Data transpilation) para asegurar que todos los datos se transpolan correctamente
4. **Testing completo** con datos reales

---

## 📞 Contacto / Soporte

Para problemas con DaisySMS:
- Email: support@daisysms.com
- Documentación: https://daisysms.com/docs/api

---

**Versión:** 1.1.0  
**Fecha:** 1 Febrero 2026  
**Desarrollador:** SMS Rental System  
