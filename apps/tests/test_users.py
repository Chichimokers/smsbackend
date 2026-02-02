"""
Tests for User model and authentication.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test cases for User model."""
    
    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        assert user.email == 'test@example.com'
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.check_password('testpass123')
    
    def test_create_user_without_email_raises_error(self):
        """Test that creating user without email raises error."""
        with pytest.raises(ValueError):
            User.objects.create_user(email='', password='testpass123')
    
    def test_create_superuser(self):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        assert admin.email == 'admin@example.com'
        assert admin.is_active is True
        assert admin.is_staff is True
        assert admin.is_superuser is True
    
    def test_user_str_method(self):
        """Test string representation of user."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        assert str(user) == 'test@example.com'
    
    def test_get_full_name(self):
        """Test get_full_name method."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        assert user.get_full_name() == 'John Doe'
    
    def test_get_full_name_empty(self):
        """Test get_full_name returns email when names are empty."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        assert user.get_full_name() == 'test@example.com'
    
    def test_get_short_name(self):
        """Test get_short_name method."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John'
        )
        assert user.get_short_name() == 'John'
    
    def test_email_normalized(self):
        """Test that email is normalized on creation."""
        user = User.objects.create_user(
            email='Test@EXAMPLE.com',
            password='testpass123'
        )
        assert user.email == 'Test@example.com'
