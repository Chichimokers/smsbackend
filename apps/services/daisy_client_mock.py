"""
DaisySMS API Mock Client for Testing.

This module provides a mock implementation of the DaisySMS API client
that simulates EXACTLY the same behavior as the real API, without making
actual HTTP calls.

Usage:
    Set MOCK_DAISY_SMS=true in .env to use this mock client.
    Set MOCK_DAISY_SMS=false to use the real API (costs money).

The mock simulates:
    - get_balance() - Returns realistic balance
    - get_services() - Returns real service list with actual prices
    - rent_number() - Simulates renting a number
    - get_sms_status() - Simulates SMS arrival (50% chance each poll)
    - cancel_rental() - Simulates cancellation
"""

import logging
import random
from decimal import Decimal
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from django.utils import timezone

from .daisy_client import (
    DaisySMSError,
    InsufficientBalanceError,
    NoNumbersAvailableError,
    MaxPriceExceededError,
    TooManyActiveRentalsError,
    RentalNotFoundError,
    RentalStatus,
    RentalResult,
    SMSResult,
    ServiceInfo,
)

logger = logging.getLogger(__name__)


# ============================================================================
# MOCK DATA - Realistic services with actual DaisySMS prices
# ============================================================================

MOCK_SERVICES_DATA = [
    # Popular services
    {'code': 'wa', 'name': 'WhatsApp', 'price': '0.25', 'count': 100, 'multi': False},
    {'code': 'go', 'name': 'Google', 'price': '0.30', 'count': 50, 'multi': True},
    {'code': 'tg', 'name': 'Telegram', 'price': '0.20', 'count': 75, 'multi': False},
    {'code': 'ig', 'name': 'Instagram', 'price': '0.35', 'count': 40, 'multi': False},
    {'code': 'fb', 'name': 'Facebook', 'price': '0.30', 'count': 60, 'multi': False},
    {'code': 'tw', 'name': 'Twitter/X', 'price': '0.40', 'count': 30, 'multi': False},
    {'code': 'ds', 'name': 'Discord', 'price': '0.25', 'count': 80, 'multi': False},
    {'code': 'ti', 'name': 'TikTok', 'price': '0.35', 'count': 45, 'multi': False},
    {'code': 'ai', 'name': 'OpenAI', 'price': '0.50', 'count': 20, 'multi': False},
    {'code': 'sp', 'name': 'Spotify', 'price': '0.30', 'count': 35, 'multi': False},
    {'code': 'nf', 'name': 'Netflix', 'price': '0.45', 'count': 25, 'multi': False},
    {'code': 'am', 'name': 'Amazon', 'price': '0.40', 'count': 30, 'multi': True},
    {'code': 'ms', 'name': 'Microsoft', 'price': '0.35', 'count': 40, 'multi': True},
    {'code': 'ap', 'name': 'Apple', 'price': '0.50', 'count': 15, 'multi': False},
    {'code': 'ub', 'name': 'Uber', 'price': '0.30', 'count': 50, 'multi': False},
    {'code': 'vi', 'name': 'Viber', 'price': '0.20', 'count': 60, 'multi': False},
    {'code': 'li', 'name': 'LinkedIn', 'price': '0.40', 'count': 25, 'multi': False},
    {'code': 'sn', 'name': 'Snapchat', 'price': '0.35', 'count': 35, 'multi': False},
]

# SMS text templates for different services
SMS_TEMPLATES = {
    'wa': 'Your WhatsApp code is {code}. Do not share this code.',
    'go': 'G-{code} is your Google verification code.',
    'tg': 'Telegram code: {code}',
    'ig': '{code} is your Instagram code. Don\'t share it.',
    'fb': '{code} is your Facebook confirmation code.',
    'tw': 'Your Twitter verification code is {code}.',
    'ds': 'Your Discord verification code is {code}.',
    'ti': '{code} is your verification code for TikTok.',
    'ai': 'Your OpenAI verification code is: {code}',
    'sp': 'Your Spotify code is {code}. Don\'t share it.',
    'nf': 'Your Netflix verification code is {code}.',
    'am': 'Your Amazon OTP is {code}. Don\'t share.',
    'ms': 'Your Microsoft account verification code is {code}',
    'ap': 'Your Apple ID verification code is: {code}',
    'ub': 'Your Uber code is {code}.',
    'vi': 'Viber code: {code}',
    'li': 'Your LinkedIn verification code is {code}.',
    'sn': 'Your Snapchat code is {code}. Don\'t share.',
}

# US Area codes for realistic phone numbers
US_AREA_CODES = [
    '201', '202', '203', '205', '206', '207', '208', '209', '210',
    '212', '213', '214', '215', '216', '217', '218', '219', '224',
    '225', '228', '229', '231', '234', '239', '240', '248', '251',
    '252', '253', '254', '256', '260', '262', '267', '269', '270',
    '281', '301', '302', '303', '304', '305', '307', '308', '309',
    '310', '312', '313', '314', '315', '316', '317', '318', '319',
    '320', '321', '323', '325', '330', '331', '334', '336', '337',
    '339', '347', '351', '352', '360', '361', '386', '401', '402',
    '404', '405', '406', '407', '408', '409', '410', '412', '413',
    '414', '415', '417', '419', '423', '424', '425', '430', '432',
    '434', '435', '440', '442', '443', '469', '470', '475', '478',
    '479', '480', '484', '501', '502', '503', '504', '505', '507',
    '508', '509', '510', '512', '513', '515', '516', '517', '518',
    '520', '530', '531', '540', '541', '551', '559', '561', '562',
    '563', '567', '570', '571', '573', '574', '575', '580', '585',
]


class DaisySMSClientMock:
    """
    Mock implementation of DaisySMS API client.
    
    Simulates EXACTLY the same behavior as the real API:
    - Same method signatures
    - Same return types
    - Same exceptions
    - Same data structures
    
    Perfect for testing without spending money.
    """
    
    def __init__(self, api_key: str = None, api_url: str = None):
        """
        Initialize mock client.
        
        Args are ignored but accepted for compatibility with real client.
        """
        # Internal state
        self._mock_balance = Decimal('100.00')  # $100 USD balance
        self._mock_rentals: Dict[int, Dict[str, Any]] = {}  # Active rentals
        self._mock_sms: Dict[int, Dict[str, Any]] = {}  # Received SMS
        self._rental_counter = 100000  # Starting rental ID
        
        logger.info('DaisySMS MOCK client initialized')
    
    def _generate_rental_id(self) -> int:
        """Generate unique rental ID like DaisySMS."""
        self._rental_counter += 1
        return self._rental_counter + random.randint(0, 10000)
    
    def _generate_phone_number(self) -> str:
        """Generate realistic US phone number."""
        area_code = random.choice(US_AREA_CODES)
        exchange = random.randint(200, 999)
        subscriber = random.randint(1000, 9999)
        return f"1{area_code}{exchange}{subscriber}"
    
    def _generate_sms_code(self) -> str:
        """Generate 6-digit SMS verification code."""
        return str(random.randint(100000, 999999))
    
    def _get_sms_text(self, service_code: str, code: str) -> str:
        """Get SMS text for a service with the code."""
        template = SMS_TEMPLATES.get(service_code, 'Your verification code is {code}')
        return template.format(code=code)
    
    def get_balance(self) -> Decimal:
        """
        Get mock account balance.
        
        Returns:
            Decimal: Balance in USD (simulates $100)
        
        Simulates: ACCESS_BALANCE:100.00
        """
        logger.debug(f'MOCK get_balance() -> {self._mock_balance}')
        return self._mock_balance
    
    def get_services(self, use_cache: bool = True) -> List[ServiceInfo]:
        """
        Get list of available services with prices.
        
        Args:
            use_cache: Ignored in mock (for compatibility)
        
        Returns:
            List of ServiceInfo with realistic prices
        
        Simulates: getPrices API response
        """
        services = []
        for svc in MOCK_SERVICES_DATA:
            service = ServiceInfo(
                service_code=svc['code'],
                name=svc['name'],
                price_usd=Decimal(svc['price']),
                available_numbers=svc['count'],
                supports_multiple_sms=svc['multi'],
                country='187'  # USA
            )
            services.append(service)
        
        logger.debug(f'MOCK get_services() -> {len(services)} services')
        return services
    
    def rent_number(
        self,
        service_code: str,
        max_price_usd: Optional[Decimal] = None,
        areas: Optional[str] = None,
        carriers: Optional[str] = None,
        number: Optional[str] = None
    ) -> RentalResult:
        """
        Rent a phone number for a service.
        
        Args:
            service_code: Service code (e.g., 'wa' for WhatsApp)
            max_price_usd: Maximum price willing to pay
            areas: Area codes (e.g., '212,718') - adds 20% to price
            carriers: Carriers (e.g., 'tmo,vz') - adds 20% to price
            number: Specific number (e.g., '11112223344') - adds 20% to price
        
        Returns:
            RentalResult with rental_id, phone_number, price_usd
        
        Raises:
            NoNumbersAvailableError: If service not found
            MaxPriceExceededError: If price > max_price
            TooManyActiveRentalsError: If too many active rentals (>20)
        
        Simulates: getNumber API response
        """
        # Find service
        service = None
        for svc in MOCK_SERVICES_DATA:
            if svc['code'] == service_code:
                service = svc
                break
        
        if not service:
            logger.warning(f'MOCK rent_number({service_code}) -> NO_NUMBERS')
            raise NoNumbersAvailableError(f'No numbers available for {service_code}')
        
        price = Decimal(service['price'])
        
        # Apply 20% markup if special options requested
        if areas or carriers or number:
            price = price * Decimal('1.20')
        
        # Check max price
        if max_price_usd is not None and price > max_price_usd:
            logger.warning(f'MOCK rent_number({service_code}) -> MAX_PRICE_EXCEEDED')
            raise MaxPriceExceededError(f'Price {price} exceeds max {max_price_usd}')
        
        # Check balance
        if self._mock_balance < price:
            logger.warning(f'MOCK rent_number({service_code}) -> NO_MONEY')
            raise InsufficientBalanceError('Insufficient balance')
        
        # Check active rentals limit (DaisySMS limit is 20)
        if len(self._mock_rentals) >= 20:
            logger.warning(f'MOCK rent_number({service_code}) -> TOO_MANY_ACTIVE')
            raise TooManyActiveRentalsError('Too many active rentals')
        
        # Generate rental
        rental_id = self._generate_rental_id()
        phone_number = self._generate_phone_number()
        
        # Deduct balance
        self._mock_balance -= price
        
        # Store rental
        self._mock_rentals[rental_id] = {
            'service_code': service_code,
            'phone_number': phone_number,
            'price_usd': price,
            'created_at': timezone.now(),
            'status': RentalStatus.WAITING,
            'poll_count': 0,  # Track polling for SMS simulation
        }
        
        result = RentalResult(
            rental_id=rental_id,
            phone_number=phone_number,
            price_usd=price
        )
        
        logger.info(
            f'MOCK rent_number({service_code}) -> '
            f'rental_id={rental_id}, phone={phone_number}, price=${price}'
        )
        
        return result
    
    def get_sms_status(self, rental_id: int, include_text: bool = True) -> SMSResult:
        """
        Check SMS status for a rental.
        
        Args:
            rental_id: The rental ID
            include_text: Whether to include full SMS text
        
        Returns:
            SMSResult with status and optional code/text
        
        Raises:
            RentalNotFoundError: If rental doesn't exist
        
        Simulates: getStatus API response
        
        SMS Simulation Logic:
            - First 2 polls: Always WAITING (simulates real delay)
            - After that: 50% chance SMS arrives each poll
            - Once SMS arrives, it's stored and returned consistently
        """
        # Check if rental exists
        if rental_id not in self._mock_rentals:
            logger.warning(f'MOCK get_sms_status({rental_id}) -> NO_ACTIVATION')
            raise RentalNotFoundError(f'Rental {rental_id} not found')
        
        rental = self._mock_rentals[rental_id]
        
        # If SMS already received, return it
        if rental_id in self._mock_sms:
            sms = self._mock_sms[rental_id]
            logger.debug(f'MOCK get_sms_status({rental_id}) -> STATUS_OK (cached)')
            return SMSResult(
                status=RentalStatus.OK,
                code=sms['code'],
                text=sms['text'] if include_text else None
            )
        
        # Increment poll count
        rental['poll_count'] += 1
        
        # First 2 polls always wait (simulate real-world delay)
        if rental['poll_count'] <= 2:
            logger.debug(f'MOCK get_sms_status({rental_id}) -> STATUS_WAIT_CODE (poll #{rental["poll_count"]})')
            return SMSResult(status=RentalStatus.WAITING)
        
        # After that, 50% chance SMS arrives
        if random.random() < 0.5:
            # SMS arrived!
            code = self._generate_sms_code()
            text = self._get_sms_text(rental['service_code'], code)
            
            self._mock_sms[rental_id] = {
                'code': code,
                'text': text,
                'received_at': timezone.now()
            }
            
            rental['status'] = RentalStatus.OK
            
            logger.info(f'MOCK get_sms_status({rental_id}) -> STATUS_OK:{code}')
            
            return SMSResult(
                status=RentalStatus.OK,
                code=code,
                text=text if include_text else None
            )
        
        # Still waiting
        logger.debug(f'MOCK get_sms_status({rental_id}) -> STATUS_WAIT_CODE (poll #{rental["poll_count"]})')
        return SMSResult(status=RentalStatus.WAITING)
    
    def cancel_rental(self, rental_id: int) -> bool:
        """
        Cancel a rental and simulate refund.
        
        Args:
            rental_id: The rental ID to cancel
        
        Returns:
            True if cancelled successfully
        
        Raises:
            RentalNotFoundError: If rental not found or already has SMS
        
        Simulates: setStatus with status=8
        """
        # Check if rental exists
        if rental_id not in self._mock_rentals:
            logger.warning(f'MOCK cancel_rental({rental_id}) -> NO_ACTIVATION')
            raise RentalNotFoundError(f'Rental {rental_id} not found')
        
        # Cannot cancel if SMS already received (like real DaisySMS)
        if rental_id in self._mock_sms:
            logger.warning(f'MOCK cancel_rental({rental_id}) -> ACCESS_READY (has SMS)')
            raise RentalNotFoundError(f'Rental {rental_id} already has SMS, cannot cancel')
        
        rental = self._mock_rentals[rental_id]
        
        # Refund balance
        self._mock_balance += rental['price_usd']
        
        # Remove rental
        del self._mock_rentals[rental_id]
        
        logger.info(f'MOCK cancel_rental({rental_id}) -> ACCESS_CANCEL (refunded ${rental["price_usd"]})')
        
        return True
    
    def mark_done(self, rental_id: int) -> bool:
        """
        Mark a rental as done (no more SMS needed).
        
        Args:
            rental_id: The rental ID
        
        Returns:
            True if marked successfully
        
        Raises:
            RentalNotFoundError: If rental not found
        
        Simulates: setStatus with status=6
        """
        if rental_id not in self._mock_rentals:
            logger.warning(f'MOCK mark_done({rental_id}) -> NO_ACTIVATION')
            raise RentalNotFoundError(f'Rental {rental_id} not found')
        
        # Remove from active rentals
        del self._mock_rentals[rental_id]
        
        # Also remove SMS if exists
        if rental_id in self._mock_sms:
            del self._mock_sms[rental_id]
        
        logger.info(f'MOCK mark_done({rental_id}) -> ACCESS_ACTIVATION')
        
        return True
    
    # =========================================================================
    # Helper methods for testing
    # =========================================================================
    
    def force_sms_arrival(self, rental_id: int, code: str = None) -> SMSResult:
        """
        Force SMS to arrive for a rental (useful for deterministic tests).
        
        Args:
            rental_id: The rental ID
            code: Optional specific code (auto-generated if not provided)
        
        Returns:
            SMSResult with the forced SMS
        """
        if rental_id not in self._mock_rentals:
            raise RentalNotFoundError(f'Rental {rental_id} not found')
        
        rental = self._mock_rentals[rental_id]
        
        if code is None:
            code = self._generate_sms_code()
        
        text = self._get_sms_text(rental['service_code'], code)
        
        self._mock_sms[rental_id] = {
            'code': code,
            'text': text,
            'received_at': timezone.now()
        }
        
        rental['status'] = RentalStatus.OK
        
        logger.info(f'MOCK force_sms_arrival({rental_id}) -> code={code}')
        
        return SMSResult(
            status=RentalStatus.OK,
            code=code,
            text=text
        )
    
    def get_active_rentals_count(self) -> int:
        """Get count of active mock rentals."""
        return len(self._mock_rentals)
    
    def reset(self):
        """Reset mock state (useful between tests)."""
        self._mock_balance = Decimal('100.00')
        self._mock_rentals = {}
        self._mock_sms = {}
        self._rental_counter = 100000
        logger.info('MOCK client reset')
