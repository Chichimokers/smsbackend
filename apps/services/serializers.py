"""
Serializers for Services app.
"""

from rest_framework import serializers
from decimal import Decimal

from apps.accounts.models import ExchangeRate


class ServiceSerializer(serializers.Serializer):
    """Serializer for service information from DaisySMS."""
    
    service_code = serializers.CharField()
    name = serializers.CharField()
    price_usd = serializers.DecimalField(max_digits=10, decimal_places=4)
    price_cup = serializers.SerializerMethodField()
    available_numbers = serializers.IntegerField()
    supports_multiple_sms = serializers.BooleanField()
    country = serializers.CharField()
    country_name = serializers.SerializerMethodField()
    
    # Country codes mapping
    COUNTRY_NAMES = {
        '187': 'USA',
        '1': 'Russia',
        '7': 'Kazakhstan',
        '86': 'China',
        '91': 'India',
        '44': 'UK',
        '49': 'Germany',
        '33': 'France',
        '34': 'Spain',
        '39': 'Italy',
    }
    
    def get_price_cup(self, obj):
        """Convert USD price to CUP."""
        price_usd = obj.price_usd if hasattr(obj, 'price_usd') else obj.get('price_usd', 0)
        return str(ExchangeRate.usd_to_cup(price_usd))
    
    def get_country_name(self, obj):
        """Get human-readable country name."""
        country = obj.country if hasattr(obj, 'country') else obj.get('country', '')
        return self.COUNTRY_NAMES.get(country, country)


class ServiceListResponseSerializer(serializers.Serializer):
    """Serializer for list of services response."""
    
    services = ServiceSerializer(many=True)
    exchange_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    cached = serializers.BooleanField(default=False)
