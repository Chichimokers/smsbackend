"""
Custom User model for SMS Rental Platform.
"""

import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)  # Superusers are auto-verified
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model using email instead of username."""
    
    email = models.EmailField(
        'email',
        unique=True,
        error_messages={
            'unique': 'Ya existe un usuario con este email.',
        }
    )
    first_name = models.CharField('nombre', max_length=150, blank=True)
    last_name = models.CharField('apellido', max_length=150, blank=True)
    google_id = models.CharField('Google ID', max_length=255, blank=True, null=True, unique=True)
    
    # Email verification fields
    is_verified = models.BooleanField(
        'verificado',
        default=False,
        help_text='Indica si el usuario ha verificado su email.',
    )
    verification_token = models.UUIDField(
        'token de verificación',
        default=uuid.uuid4,
        unique=True,
        help_text='Token único para verificar el email.',
    )
    verification_token_created_at = models.DateTimeField(
        'fecha de creación del token',
        auto_now_add=True,
    )
    
    is_staff = models.BooleanField(
        'staff status',
        default=False,
        help_text='Designates whether the user can log into this admin site.',
    )
    is_active = models.BooleanField(
        'active',
        default=True,
        help_text='Designates whether this user should be treated as active.',
    )
    date_joined = models.DateTimeField('fecha de registro', default=timezone.now)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.email
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.email.split('@')[0]
    
    def regenerate_verification_token(self):
        """Generate a new verification token."""
        self.verification_token = uuid.uuid4()
        self.verification_token_created_at = timezone.now()
        self.save(update_fields=['verification_token', 'verification_token_created_at'])
        return self.verification_token
    
    def verify_email(self):
        """Mark the user as verified."""
        self.is_verified = True
        self.save(update_fields=['is_verified'])
