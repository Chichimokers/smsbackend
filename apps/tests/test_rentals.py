"""
Tests for Rental models.
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.rentals.models import PhoneRental, SMS

User = get_user_model()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        email='testuser@example.com',
        password='testpass123'
    )


@pytest.fixture
def test_rental(test_user):
    """Create a test rental."""
    return PhoneRental.objects.create(
        user=test_user,
        daisy_rental_id=123456,
        phone_number='12025551234',
        service_code='wa',
        service_name='WhatsApp',
        country='187',
        price_usd=Decimal('0.25'),
        price_cup=Decimal('1200.00'),
        expires_at=timezone.now() + timedelta(seconds=420)
    )


@pytest.mark.django_db
class TestPhoneRentalModel:
    """Test cases for PhoneRental model."""
    
    def test_create_rental(self, test_user):
        """Test creating a phone rental."""
        rental = PhoneRental.objects.create(
            user=test_user,
            daisy_rental_id=123456,
            phone_number='12025551234',
            service_code='wa',
            service_name='WhatsApp',
            price_usd=Decimal('0.25'),
            price_cup=Decimal('1200.00'),
            expires_at=timezone.now() + timedelta(seconds=420)
        )
        
        assert rental.user == test_user
        assert rental.daisy_rental_id == 123456
        assert rental.phone_number == '12025551234'
        assert rental.service_code == 'wa'
        assert rental.status == PhoneRental.RentalStatus.ACTIVE
        assert rental.refunded is False
    
    def test_rental_str_method(self, test_rental):
        """Test string representation of rental."""
        expected = f'{test_rental.phone_number} ({test_rental.service_name}) - {test_rental.user.email}'
        assert str(test_rental) == expected
    
    def test_rental_is_active(self, test_rental):
        """Test is_active property."""
        assert test_rental.is_active is True
    
    def test_rental_is_expired(self, test_user):
        """Test is_expired property."""
        expired_rental = PhoneRental.objects.create(
            user=test_user,
            daisy_rental_id=999999,
            phone_number='12025559999',
            service_code='tg',
            service_name='Telegram',
            price_usd=Decimal('0.20'),
            price_cup=Decimal('960.00'),
            expires_at=timezone.now() - timedelta(minutes=5)  # Already expired
        )
        
        assert expired_rental.is_expired is True
        assert expired_rental.is_active is False
    
    def test_remaining_time_seconds(self, test_rental):
        """Test remaining_time_seconds property."""
        remaining = test_rental.remaining_time_seconds
        assert remaining > 0
        assert remaining <= 420  # Max 420 seconds (7 minutes)
    
    def test_formatted_phone(self, test_rental):
        """Test formatted_phone property."""
        assert test_rental.formatted_phone == '+12025551234'
    
    def test_formatted_phone_already_has_plus(self, test_user):
        """Test formatted_phone when number already has plus."""
        rental = PhoneRental.objects.create(
            user=test_user,
            daisy_rental_id=111111,
            phone_number='+12025551111',
            service_code='go',
            service_name='Google',
            price_usd=Decimal('0.30'),
            price_cup=Decimal('1440.00'),
            expires_at=timezone.now() + timedelta(seconds=420)
        )
        assert rental.formatted_phone == '+12025551111'
    
    def test_mark_sms_received(self, test_rental):
        """Test mark_sms_received method."""
        test_rental.mark_sms_received()
        assert test_rental.status == PhoneRental.RentalStatus.SMS_RECEIVED
    
    def test_mark_expired(self, test_rental):
        """Test mark_expired method."""
        test_rental.mark_expired()
        assert test_rental.status == PhoneRental.RentalStatus.EXPIRED
    
    def test_mark_cancelled(self, test_rental):
        """Test mark_cancelled method."""
        test_rental.mark_cancelled()
        assert test_rental.status == PhoneRental.RentalStatus.CANCELLED
    
    def test_mark_refunded(self, test_rental):
        """Test mark_refunded method."""
        test_rental.mark_refunded()
        assert test_rental.status == PhoneRental.RentalStatus.REFUNDED
        assert test_rental.refunded is True
    
    def test_mark_completed(self, test_rental):
        """Test mark_completed method."""
        test_rental.mark_completed()
        assert test_rental.status == PhoneRental.RentalStatus.COMPLETED


@pytest.mark.django_db
class TestSMSModel:
    """Test cases for SMS model."""
    
    def test_create_sms(self, test_rental):
        """Test creating an SMS record."""
        sms = SMS.objects.create(
            phone_rental=test_rental,
            code='123456',
            text='Your WhatsApp code is 123456'
        )
        
        assert sms.phone_rental == test_rental
        assert sms.code == '123456'
        assert sms.text == 'Your WhatsApp code is 123456'
    
    def test_sms_str_method(self, test_rental):
        """Test string representation of SMS."""
        sms = SMS.objects.create(
            phone_rental=test_rental,
            code='654321',
            text='Your code is 654321'
        )
        expected = f'SMS para {test_rental.phone_number}: 654321'
        assert str(sms) == expected
    
    def test_create_from_daisy_response(self, test_rental):
        """Test create_from_daisy_response class method."""
        sms = SMS.create_from_daisy_response(
            phone_rental=test_rental,
            code='999888',
            text='G-999888 is your Google verification code.'
        )
        
        assert sms.code == '999888'
        assert sms.text == 'G-999888 is your Google verification code.'
        
        # Refresh rental from db
        test_rental.refresh_from_db()
        assert test_rental.status == PhoneRental.RentalStatus.SMS_RECEIVED
