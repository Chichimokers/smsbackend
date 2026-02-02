"""
Pytest configuration and fixtures.
"""

import pytest
import os
import django

# Set up Django settings for pytest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


@pytest.fixture(scope='session')
def django_db_setup():
    """Set up test database."""
    pass


@pytest.fixture
def api_client():
    """Create a DRF API client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Create an authenticated API client."""
    from rest_framework_simplejwt.tokens import RefreshToken
    
    refresh = RefreshToken.for_user(test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def test_user(db):
    """Create a test user."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = User.objects.create_user(
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    return user


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    admin = User.objects.create_superuser(
        email='admin@example.com',
        password='adminpass123'
    )
    return admin


@pytest.fixture
def mock_daisy_client():
    """Create a mock DaisySMS client."""
    from apps.services.daisy_client_mock import DaisySMSClientMock
    client = DaisySMSClientMock()
    return client
