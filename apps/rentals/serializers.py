"""
Serializers for Rentals app.

Simplified serializers - views build responses manually for flexibility.
Only RentNumberSerializer (input validation) and SMSSerializer (nested output) are used.
"""

from rest_framework import serializers

from .models import SMS


# Valid country codes from DaisySMS (sms-activate compatible)
VALID_COUNTRY_CODES = {
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '14', '15',
    '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28',
    '29', '30', '31', '32', '33', '34', '36', '37', '38', '39', '40', '41', '43',
    '44', '46', '47', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58',
    '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71',
    '72', '73', '74', '75', '76', '77', '78', '79', '80', '81', '82', '83', '84',
    '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96', '97',
    '98', '99', '100', '101', '102', '117', '129', '187',
}


class SMSSerializer(serializers.ModelSerializer):
    """Serializer for SMS model - used in rental list responses."""
    
    class Meta:
        model = SMS
        fields = ['id', 'code', 'text', 'received_at', 'created_at']
        read_only_fields = fields


class RentNumberSerializer(serializers.Serializer):
    """Serializer for renting a number request - input validation."""
    
    service_code = serializers.CharField(
        max_length=10,
        help_text='Codigo del servicio (ej: wa, go, tg)'
    )
    max_price_usd = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        required=False,
        allow_null=True,
        help_text='Precio maximo en USD (opcional)'
    )
    country = serializers.CharField(
        max_length=10,
        required=False,
        default='187',
        help_text='Codigo del pais (default: 187 para USA). Codigos comunes: 187=USA, 18=UK, 36=Canada, 40=Germany, 0=Russia'
    )
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
    
    def validate_country(self, value):
        """Validate country code is valid."""
        if value not in VALID_COUNTRY_CODES:
            raise serializers.ValidationError(
                f'Codigo de pais invalido: {value}. '
                f'Codigos comunes: 187=USA, 18=UK, 36=Canada, 40=Germany, 0=Russia, 85=India'
            )
        return value
    
    def validate_areas(self, value):
        """Validate area codes format."""
        if value:
            # Remove spaces and validate format (comma-separated numbers)
            areas = value.replace(' ', '')
            for area in areas.split(','):
                if area and not area.isdigit():
                    raise serializers.ValidationError(
                        f'Formato de area invalido: {area}. Use numeros separados por comas (ej: 212,718)'
                    )
            return areas
        return value
    
    def validate_carriers(self, value):
        """Validate carriers format."""
        if value:
            valid_carriers = {'tmo', 'vz', 'att'}
            carriers = value.lower().replace(' ', '')
            for carrier in carriers.split(','):
                if carrier and carrier not in valid_carriers:
                    raise serializers.ValidationError(
                        f'Carrier invalido: {carrier}. Carriers validos: tmo (T-Mobile), vz (Verizon), att (AT&T)'
                    )
            return carriers
        return value
    
    def validate_number(self, value):
        """Validate specific number format."""
        if value:
            # Remove any non-digit characters
            number = ''.join(filter(str.isdigit, value))
            if len(number) < 10 or len(number) > 15:
                raise serializers.ValidationError(
                    f'Numero invalido: {value}. Debe tener entre 10 y 15 digitos'
                )
            return number
        return value
