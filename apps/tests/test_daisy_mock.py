"""
Tests for DaisySMS Mock Client.
"""

import pytest
from decimal import Decimal

from apps.services.daisy_client_mock import DaisySMSClientMock
from apps.services.daisy_client import (
    RentalStatus,
    NoNumbersAvailableError,
    MaxPriceExceededError,
    RentalNotFoundError,
)


@pytest.fixture
def mock_client():
    """Create a fresh mock client for each test."""
    client = DaisySMSClientMock()
    return client


class TestDaisySMSClientMock:
    """Test cases for DaisySMS Mock Client."""
    
    def test_get_balance(self, mock_client):
        """Test get_balance returns expected balance."""
        balance = mock_client.get_balance()
        assert balance == Decimal('100.00')
    
    def test_get_services(self, mock_client):
        """Test get_services returns list of services."""
        services = mock_client.get_services()
        assert len(services) > 0
        
        # Check structure of first service
        service = services[0]
        assert hasattr(service, 'service_code')
        assert hasattr(service, 'name')
        assert hasattr(service, 'price_usd')
        assert hasattr(service, 'available_numbers')
    
    def test_get_services_includes_whatsapp(self, mock_client):
        """Test that WhatsApp service is included."""
        services = mock_client.get_services()
        wa_services = [s for s in services if s.service_code == 'wa']
        assert len(wa_services) == 1
        assert wa_services[0].name == 'WhatsApp'
    
    def test_rent_number_success(self, mock_client):
        """Test renting a number successfully."""
        result = mock_client.rent_number('wa')
        
        assert result.rental_id > 0
        assert len(result.phone_number) == 11  # US format: 1XXXXXXXXXX
        assert result.phone_number.startswith('1')
        assert result.price_usd == Decimal('0.25')
    
    def test_rent_number_invalid_service(self, mock_client):
        """Test renting with invalid service code raises error."""
        with pytest.raises(NoNumbersAvailableError):
            mock_client.rent_number('invalid_service')
    
    def test_rent_number_max_price_exceeded(self, mock_client):
        """Test renting with low max_price raises error."""
        with pytest.raises(MaxPriceExceededError):
            mock_client.rent_number('wa', max_price_usd=Decimal('0.01'))
    
    def test_get_sms_status_first_polls_waiting(self, mock_client):
        """Test that first 2 polls always return WAITING."""
        result = mock_client.rent_number('wa')
        rental_id = result.rental_id
        
        # First poll
        status1 = mock_client.get_sms_status(rental_id)
        assert status1.status == RentalStatus.WAITING
        
        # Second poll
        status2 = mock_client.get_sms_status(rental_id)
        assert status2.status == RentalStatus.WAITING
    
    def test_get_sms_status_not_found(self, mock_client):
        """Test get_sms_status with invalid rental_id raises error."""
        with pytest.raises(RentalNotFoundError):
            mock_client.get_sms_status(999999)
    
    def test_force_sms_arrival(self, mock_client):
        """Test force_sms_arrival helper method."""
        result = mock_client.rent_number('wa')
        rental_id = result.rental_id
        
        # Force SMS arrival
        sms = mock_client.force_sms_arrival(rental_id, code='123456')
        
        assert sms.status == RentalStatus.OK
        assert sms.code == '123456'
        assert 'WhatsApp' in sms.text
        
        # Subsequent calls should return same SMS
        status = mock_client.get_sms_status(rental_id)
        assert status.status == RentalStatus.OK
        assert status.code == '123456'
    
    def test_cancel_rental_success(self, mock_client):
        """Test cancelling a rental."""
        result = mock_client.rent_number('wa')
        rental_id = result.rental_id
        
        initial_balance = mock_client.get_balance()
        
        # Cancel
        cancelled = mock_client.cancel_rental(rental_id)
        assert cancelled is True
        
        # Balance should be refunded
        new_balance = mock_client.get_balance()
        assert new_balance > initial_balance
    
    def test_cancel_rental_not_found(self, mock_client):
        """Test cancelling non-existent rental raises error."""
        with pytest.raises(RentalNotFoundError):
            mock_client.cancel_rental(999999)
    
    def test_cancel_rental_with_sms_fails(self, mock_client):
        """Test cancelling rental with SMS already received fails."""
        result = mock_client.rent_number('wa')
        rental_id = result.rental_id
        
        # Force SMS arrival
        mock_client.force_sms_arrival(rental_id)
        
        # Try to cancel - should fail
        with pytest.raises(RentalNotFoundError):
            mock_client.cancel_rental(rental_id)
    
    def test_mark_done(self, mock_client):
        """Test marking rental as done."""
        result = mock_client.rent_number('wa')
        rental_id = result.rental_id
        
        done = mock_client.mark_done(rental_id)
        assert done is True
        
        # Rental should be removed
        with pytest.raises(RentalNotFoundError):
            mock_client.get_sms_status(rental_id)
    
    def test_reset(self, mock_client):
        """Test reset method clears state."""
        # Create some rentals
        mock_client.rent_number('wa')
        mock_client.rent_number('tg')
        
        assert mock_client.get_active_rentals_count() == 2
        
        # Reset
        mock_client.reset()
        
        assert mock_client.get_active_rentals_count() == 0
        assert mock_client.get_balance() == Decimal('100.00')
    
    def test_balance_deducted_on_rent(self, mock_client):
        """Test balance is deducted when renting."""
        initial_balance = mock_client.get_balance()
        
        result = mock_client.rent_number('wa')
        
        new_balance = mock_client.get_balance()
        assert new_balance == initial_balance - result.price_usd
