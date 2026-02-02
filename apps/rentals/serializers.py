"""
Serializers for Rentals app.

Simplified serializers - views build responses manually for flexibility.
Only RentNumberSerializer (input validation) and SMSSerializer (nested output) are used.
"""

from rest_framework import serializers

from .models import SMS


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
        help_text='Codigo del pais (default: 187 para USA)'
    )
