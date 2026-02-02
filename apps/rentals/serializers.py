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
