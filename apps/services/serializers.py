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
    
    # Country codes mapping (DaisySMS uses sms-activate country codes)
    COUNTRY_NAMES = {
        '0': 'Russia',
        '1': 'Ukraine',
        '2': 'Kazakhstan',
        '3': 'China',
        '4': 'Philippines',
        '5': 'Myanmar',
        '6': 'Indonesia',
        '7': 'Malaysia',
        '8': 'Kenya',
        '9': 'Tanzania',
        '10': 'Vietnam',
        '11': 'Kyrgyzstan',
        '12': 'USA (Virtual)',
        '14': 'Egypt',
        '15': 'Israel',
        '16': 'Hong Kong',
        '17': 'Poland',
        '18': 'UK',
        '19': 'Madagascar',
        '20': 'DR Congo',
        '21': 'Nigeria',
        '22': 'Macau',
        '23': 'Estonia',
        '24': 'Sri Lanka',
        '25': 'Ivory Coast',
        '26': 'Gambia',
        '27': 'Serbia',
        '28': 'Morocco',
        '29': 'Cameroon',
        '30': 'South Africa',
        '31': 'Sweden',
        '32': 'Netherlands',
        '33': 'France',
        '34': 'Spain',
        '36': 'Canada',
        '37': 'Turkey',
        '38': 'Czech Republic',
        '39': 'Italy',
        '40': 'Germany',
        '41': 'Pakistan',
        '43': 'Ireland',
        '44': 'Portugal',
        '46': 'Azerbaijan',
        '47': 'Bangladesh',
        '49': 'Austria',
        '50': 'Brazil',
        '51': 'Romania',
        '52': 'Belgium',
        '53': 'New Zealand',
        '54': 'Australia',
        '55': 'Finland',
        '56': 'Hungary',
        '57': 'Lithuania',
        '58': 'Latvia',
        '59': 'Moldova',
        '60': 'Cambodia',
        '61': 'Ghana',
        '62': 'Colombia',
        '63': 'Peru',
        '64': 'Greece',
        '65': 'Denmark',
        '66': 'Norway',
        '67': 'Slovakia',
        '68': 'Slovenia',
        '69': 'Bulgaria',
        '70': 'Croatia',
        '71': 'Nepal',
        '72': 'Argentina',
        '73': 'Mexico',
        '74': 'Chile',
        '75': 'Uganda',
        '76': 'Uzbekistan',
        '77': 'Georgia',
        '78': 'Albania',
        '79': 'Luxembourg',
        '80': 'Switzerland',
        '81': 'Japan',
        '82': 'South Korea',
        '83': 'Taiwan',
        '84': 'Thailand',
        '85': 'India',
        '86': 'Singapore',
        '87': 'UAE',
        '88': 'Saudi Arabia',
        '89': 'Tajikistan',
        '90': 'Bolivia',
        '91': 'Costa Rica',
        '92': 'Ecuador',
        '93': 'Paraguay',
        '94': 'Uruguay',
        '95': 'Venezuela',
        '96': 'Panama',
        '97': 'Dominican Republic',
        '98': 'Guatemala',
        '99': 'El Salvador',
        '100': 'Honduras',
        '101': 'Nicaragua',
        '102': 'Puerto Rico',
        '117': 'Zambia',
        '129': 'Zimbabwe',
        '187': 'USA',
    }
    
    def get_price_cup(self, obj):
        """Convert USD price to CUP."""
        price_usd = obj.price_usd if hasattr(obj, 'price_usd') else obj.get('price_usd', 0)
        return str(ExchangeRate.usd_to_cup(price_usd))
    
    def get_country_name(self, obj):
        """Get human-readable country name."""
        country = obj.country if hasattr(obj, 'country') else obj.get('country', '')
        return self.COUNTRY_NAMES.get(str(country), f'Country {country}')


class ServiceListResponseSerializer(serializers.Serializer):
    """Serializer for list of services response."""
    
    services = ServiceSerializer(many=True)
    exchange_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    cached = serializers.BooleanField(default=False)
