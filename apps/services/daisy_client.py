"""
DaisySMS API Client Service.
Handles all communication with the DaisySMS API.
"""

import json
import logging
import requests
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class DaisySMSError(Exception):
    """Base exception for DaisySMS errors."""
    pass


class InsufficientBalanceError(DaisySMSError):
    """Raised when DaisySMS account has insufficient balance."""
    pass


class NoNumbersAvailableError(DaisySMSError):
    """Raised when no numbers are available for the service."""
    pass


class MaxPriceExceededError(DaisySMSError):
    """Raised when the price exceeds the max price."""
    pass


class TooManyActiveRentalsError(DaisySMSError):
    """Raised when user has too many active rentals."""
    pass


class InvalidAPIKeyError(DaisySMSError):
    """Raised when API key is invalid."""
    pass


class RentalNotFoundError(DaisySMSError):
    """Raised when rental ID is not found."""
    pass


class RentalStatus(str, Enum):
    """Status of a rental from DaisySMS."""
    WAITING = 'STATUS_WAIT_CODE'
    OK = 'STATUS_OK'
    CANCEL = 'STATUS_CANCEL'


@dataclass
class RentalResult:
    """Result of renting a number."""
    rental_id: int
    phone_number: str
    price_usd: Decimal


@dataclass
class SMSResult:
    """Result of checking for SMS."""
    status: str
    code: Optional[str] = None
    text: Optional[str] = None


@dataclass
class ServiceInfo:
    """Information about a service from DaisySMS."""
    service_code: str
    name: str
    price_usd: Decimal
    available_numbers: int
    supports_multiple_sms: bool
    country: str


class DaisySMSClient:
    """
    Client for interacting with the DaisySMS API.
    
    API Documentation: https://daisysms.com/docs/api
    """
    
    # Mapping of service codes to human-readable names
    SERVICE_NAMES = {
        'wa': 'WhatsApp',
        'go': 'Google',
        'tg': 'Telegram',
        'ig': 'Instagram',
        'fb': 'Facebook',
        'tw': 'Twitter/X',
        'ds': 'Discord',
        'vi': 'Viber',
        'wx': 'WeChat',
        'ap': 'Apple',
        'ms': 'Microsoft',
        'am': 'Amazon',
        'nf': 'Netflix',
        'sp': 'Spotify',
        'ub': 'Uber',
        'ly': 'Lyft',
        'ai': 'OpenAI',
        'ti': 'TikTok',
        'sn': 'Snapchat',
        'li': 'LinkedIn',
        'ya': 'Yahoo',
        'ol': 'OLX',
        'av': 'Avito',
        'mm': 'Mercado Libre',
        'ot': 'Otro',
    }
    
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
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """Initialize the DaisySMS client."""
        self.api_key = api_key or settings.DAISY_SMS_API_KEY
        self.api_url = api_url or settings.DAISY_SMS_API_URL
        self.timeout = 30  # seconds
        
        if not self.api_key:
            raise ValueError('DAISY_SMS_API_KEY is not configured')
    
    def _make_request(self, params: Dict[str, Any], include_headers: bool = False) -> Any:
        """
        Make a request to the DaisySMS API.
        
        Args:
            params: Query parameters for the request
            include_headers: Whether to return headers along with response
            
        Returns:
            Response text or tuple of (text, headers) if include_headers is True
        """
        params['api_key'] = self.api_key
        
        try:
            response = requests.get(
                self.api_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            text = response.text.strip()
            
            # Check for common errors
            if text == 'BAD_KEY':
                raise InvalidAPIKeyError('Invalid API key')
            
            if include_headers:
                return text, response.headers
            return text
            
        except requests.RequestException as e:
            logger.error(f'DaisySMS API request failed: {e}')
            raise DaisySMSError(f'API request failed: {e}')
    
    def get_balance(self) -> Decimal:
        """
        Get the account balance in USD.
        
        Returns:
            Account balance as Decimal
        """
        response = self._make_request({'action': 'getBalance'})
        
        # Response format: ACCESS_BALANCE:50.30
        if response.startswith('ACCESS_BALANCE:'):
            balance = response.split(':')[1]
            return Decimal(balance)
        
        raise DaisySMSError(f'Unexpected balance response: {response}')
    
    def get_services(self, use_cache: bool = True) -> List[ServiceInfo]:
        """
        Get list of available services with prices.
        
        Args:
            use_cache: Whether to use cached results (5 minute cache)
            
        Returns:
            List of ServiceInfo objects
            
        DaisySMS API Response Structure (getPricesVerification):
        {
            "service_code": {
                "country_code": {
                    "name": "Service Name",
                    "ttl": 420,
                    "count": 100,
                    "cost": "0.10",
                    "ltrPrice": "0.20",
                    "repeatable": true
                }
            }
        }
        """
        cache_key = 'daisy_sms_services'
        
        if use_cache:
            cached = cache.get(cache_key)
            if cached:
                logger.debug('Returning cached services')
                return cached
        
        # Use getPricesVerification for detailed service info with prices
        response = self._make_request({'action': 'getPricesVerification'})
        
        import json
        try:
            data = json.loads(response) if response else {}
        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse services response: {response[:500]}... Error: {e}')
            raise DaisySMSError('Failed to parse services response from DaisySMS')
        
        services = []
        
        # Data structure: service_code => country_code => {name, ttl, count, cost, ltrPrice, repeatable}
        for service_code, countries_data in data.items():
            if not isinstance(countries_data, dict):
                continue
            
            for country_code, service_data in countries_data.items():
                if not isinstance(service_data, dict):
                    continue
                try:
                    # DaisySMS uses 'cost' field for price
                    price = Decimal(str(service_data.get('cost', '0')))
                    count = int(service_data.get('count', 0))
                    # 'repeatable' indicates if multiple SMS can be received
                    repeatable = service_data.get('repeatable', False)
                    if isinstance(repeatable, str):
                        repeatable = repeatable.lower() == 'true'
                    
                    # Use name from API response, fallback to SERVICE_NAMES or code
                    api_name = service_data.get('name')
                    if api_name:
                        service_name = str(api_name)
                    else:
                        service_name = self.SERVICE_NAMES.get(service_code) or service_code.upper()
                    
                    service = ServiceInfo(
                        service_code=service_code,
                        name=service_name,
                        price_usd=price,
                        available_numbers=count,
                        supports_multiple_sms=bool(repeatable),
                        country=str(country_code)
                    )
                    services.append(service)
                except (ValueError, TypeError) as e:
                    logger.warning(f'Failed to parse service {service_code} for country {country_code}: {e}')
                    continue
        
        # Cache for 5 minutes
        if use_cache and services:
            cache.set(cache_key, services, timeout=settings.SERVICES_CACHE_TIMEOUT)
        
        logger.info(f'Loaded {len(services)} services from DaisySMS')
        return services
    
    def rent_number(
        self,
        service_code: str,
        max_price_usd: Optional[Decimal] = None,
        areas: Optional[str] = None,
        carriers: Optional[str] = None,
        number: Optional[str] = None,
        country: str = '187'
    ) -> RentalResult:
        """
        Rent a phone number for a service.
        
        Args:
            service_code: Service code (e.g., 'wa' for WhatsApp)
            max_price_usd: Maximum price willing to pay (optional)
            areas: Area codes (e.g., '212,718') - adds 20% to price
            carriers: Carriers (e.g., 'tmo,vz') - adds 20% to price
            number: Specific number (e.g., '11112223344') - adds 20% to price
            country: Country code (default: '187' for USA) - for interface consistency
            
        Returns:
            RentalResult with rental_id, phone_number, and price_usd
            
        Note:
            DaisySMS is a USA-focused service. The country parameter is included
            for API consistency but the actual DaisySMS API primarily serves USA numbers.
        """
        params = {
            'action': 'getNumber',
            'service': service_code,
        }
        
        if max_price_usd is not None:
            params['max_price'] = str(max_price_usd)
        
        # Add optional parameters
        if areas is not None:
            params['areas'] = areas
        if carriers is not None:
            params['carriers'] = carriers
        if number is not None:
            params['number'] = number
        
        response, headers = self._make_request(params, include_headers=True)
        
        # Check for errors
        if response == 'NO_NUMBERS':
            raise NoNumbersAvailableError(f'No numbers available for service {service_code}')
        
        if response == 'NO_MONEY':
            raise InsufficientBalanceError('Insufficient balance in DaisySMS account')
        
        if response == 'MAX_PRICE_EXCEEDED':
            raise MaxPriceExceededError('Price exceeds maximum specified')
        
        if response == 'TOO_MANY_ACTIVE_RENTALS':
            raise TooManyActiveRentalsError('Too many active rentals')
        
        # Success format: ACCESS_NUMBER:rental_id:phone_number
        if response.startswith('ACCESS_NUMBER:'):
            parts = response.split(':')
            rental_id = int(parts[1])
            phone_number = parts[2]
            
            # Get price from X-Price header
            price_usd = Decimal(headers.get('X-Price', '0'))
            
            return RentalResult(
                rental_id=rental_id,
                phone_number=phone_number,
                price_usd=price_usd
            )
        
        raise DaisySMSError(f'Unexpected rent response: {response}')
    
    def get_sms_status(self, rental_id: int, include_text: bool = True) -> SMSResult:
        """
        Check the status of a rental and get SMS if received.
        
        Args:
            rental_id: The rental ID from rent_number
            include_text: Whether to include full SMS text
            
        Returns:
            SMSResult with status and optional code/text
        """
        params = {
            'action': 'getStatus',
            'id': rental_id,
        }
        
        if include_text:
            params['text'] = '1'
        
        response, headers = self._make_request(params, include_headers=True)
        
        # Check for errors
        if response == 'NO_ACTIVATION':
            raise RentalNotFoundError(f'Rental {rental_id} not found')
        
        if response == 'STATUS_CANCEL':
            return SMSResult(status=RentalStatus.CANCEL)
        
        if response == 'STATUS_WAIT_CODE':
            return SMSResult(status=RentalStatus.WAITING)
        
        # Success format: STATUS_OK:code
        if response.startswith('STATUS_OK:'):
            code = response.split(':')[1]
            text = headers.get('X-Text', '')
            
            return SMSResult(
                status=RentalStatus.OK,
                code=code,
                text=text
            )
        
        raise DaisySMSError(f'Unexpected status response: {response}')
    
    def cancel_rental(self, rental_id: int) -> bool:
        """
        Cancel a rental and get refund.
        
        Args:
            rental_id: The rental ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        params = {
            'action': 'setStatus',
            'id': rental_id,
            'status': 8,  # Cancel status
        }
        
        response = self._make_request(params)
        
        if response == 'ACCESS_CANCEL':
            return True
        
        if response == 'ACCESS_READY':
            # Already got the code or rental missing
            raise RentalNotFoundError(f'Rental {rental_id} cannot be cancelled')
        
        if response == 'NO_ACTIVATION':
            raise RentalNotFoundError(f'Rental {rental_id} not found')
        
        raise DaisySMSError(f'Unexpected cancel response: {response}')
    
    def mark_done(self, rental_id: int) -> bool:
        """
        Mark a rental as done (no more SMS needed).
        
        Args:
            rental_id: The rental ID to mark as done
            
        Returns:
            True if marked successfully
        """
        params = {
            'action': 'setStatus',
            'id': rental_id,
            'status': 6,  # Done status
        }
        
        response = self._make_request(params)
        
        if response == 'ACCESS_ACTIVATION':
            return True
        
        if response == 'NO_ACTIVATION':
            raise RentalNotFoundError(f'Rental {rental_id} not found')
        
        raise DaisySMSError(f'Unexpected done response: {response}')


# Singleton instance for convenience
_client_instance = None


def get_daisy_client():
    """
    Get or create a DaisySMS client instance.
    
    Uses mock client if MOCK_DAISY_SMS=true in settings (for testing).
    Uses real client if MOCK_DAISY_SMS=false (costs money).
    
    Returns:
        DaisySMSClient or DaisySMSClientMock instance
    """
    global _client_instance
    if _client_instance is None:
        if settings.MOCK_DAISY_SMS:
            from apps.services.daisy_client_mock import DaisySMSClientMock
            _client_instance = DaisySMSClientMock()
            logger.info('Using DaisySMS MOCK client (MOCK_DAISY_SMS=true)')
        else:
            _client_instance = DaisySMSClient()
            logger.info('Using DaisySMS REAL client (MOCK_DAISY_SMS=false)')
    return _client_instance


def reset_daisy_client():
    """
    Reset the singleton client instance.
    
    Useful for:
    - Switching between mock/real during tests
    - Resetting mock state between tests
    """
    global _client_instance
    _client_instance = None
    logger.debug('DaisySMS client instance reset')
