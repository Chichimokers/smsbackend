"""
Models for Rentals app - PhoneRental and SMS.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta


class PhoneRental(models.Model):
    """
    Phone number rental record.
    Tracks rentals from DaisySMS associated with users.
    """
    
    class RentalStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Activo - Esperando SMS'
        SMS_RECEIVED = 'SMS_RECEIVED', 'SMS Recibido'
        EXPIRED = 'EXPIRED', 'Expirado'
        CANCELLED = 'CANCELLED', 'Cancelado'
        REFUNDED = 'REFUNDED', 'Reembolsado'
        COMPLETED = 'COMPLETED', 'Completado'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rentals',
        verbose_name='Usuario'
    )
    daisy_rental_id = models.IntegerField(
        'ID en DaisySMS',
        unique=True,
        help_text='ID del rental en el sistema de DaisySMS'
    )
    phone_number = models.CharField('Número de teléfono', max_length=20)
    service_code = models.CharField(
        'Código del servicio',
        max_length=10,
        help_text='Código del servicio (ej: wa, go, tg)'
    )
    service_name = models.CharField(
        'Nombre del servicio',
        max_length=100,
        help_text='Nombre del servicio (ej: WhatsApp, Google)'
    )
    country = models.CharField('País', max_length=10, default='187')
    
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=RentalStatus.choices,
        default=RentalStatus.ACTIVE
    )
    
    price_usd = models.DecimalField(
        'Precio USD',
        max_digits=10,
        decimal_places=4,
        help_text='Precio cobrado por DaisySMS en USD'
    )
    price_cup = models.DecimalField(
        'Precio CUP',
        max_digits=12,
        decimal_places=2,
        help_text='Precio cobrado al usuario en CUP'
    )
    
    refunded = models.BooleanField('Reembolsado', default=False)
    
    rented_at = models.DateTimeField('Fecha de alquiler', auto_now_add=True)
    expires_at = models.DateTimeField(
        'Fecha de expiración',
        help_text='Fecha y hora en que expira el alquiler'
    )
    last_polled_at = models.DateTimeField(
        'Último polling',
        null=True,
        blank=True,
        help_text='Última vez que se consultó el estado'
    )
    
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Alquiler de número'
        verbose_name_plural = 'Alquileres de números'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['daisy_rental_id']),
        ]
    
    def __str__(self):
        return f'{self.phone_number} ({self.service_name}) - {self.user.email}'
    
    @property
    def is_expired(self):
        """Check if the rental has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_active(self):
        """Check if the rental is still active."""
        return self.status == self.RentalStatus.ACTIVE and not self.is_expired
    
    @property
    def remaining_time_seconds(self):
        """Get remaining time in seconds."""
        if self.is_expired:
            return 0
        remaining = self.expires_at - timezone.now()
        return max(0, int(remaining.total_seconds()))
    
    @property
    def formatted_phone(self):
        """Get formatted phone number with + prefix."""
        if not self.phone_number.startswith('+'):
            return f'+{self.phone_number}'
        return self.phone_number
    
    def mark_sms_received(self):
        """Mark rental as SMS received."""
        self.status = self.RentalStatus.SMS_RECEIVED
        self.save()
    
    def mark_expired(self):
        """Mark rental as expired."""
        self.status = self.RentalStatus.EXPIRED
        self.save()
    
    def mark_cancelled(self):
        """Mark rental as cancelled."""
        self.status = self.RentalStatus.CANCELLED
        self.save()
    
    def mark_refunded(self):
        """Mark rental as refunded."""
        self.status = self.RentalStatus.REFUNDED
        self.refunded = True
        self.save()
    
    def mark_completed(self):
        """Mark rental as completed."""
        self.status = self.RentalStatus.COMPLETED
        self.save()
    
    @classmethod
    def get_duration_seconds(cls, service_code: str) -> int:
        """
        Get rental duration in seconds based on service code.
        WhatsApp (wa) = 420 seconds (7 minutes)
        All others = 420 seconds (7 minutes)
        """
        if service_code.lower() == 'wa':
            return settings.RENTAL_DURATION_WHATSAPP_SECONDS
        return settings.RENTAL_DURATION_DEFAULT_SECONDS
    
    @classmethod
    def create_rental(
        cls,
        user,
        daisy_rental_id: int,
        phone_number: str,
        service_code: str,
        service_name: str,
        price_usd: Decimal,
        price_cup: Decimal,
        country: str = '187',
        duration_seconds: int = None
    ):
        """Create a new rental record."""
        if duration_seconds is None:
            duration_seconds = cls.get_duration_seconds(service_code)
        
        expires_at = timezone.now() + timedelta(seconds=duration_seconds)
        
        return cls.objects.create(
            user=user,
            daisy_rental_id=daisy_rental_id,
            phone_number=phone_number,
            service_code=service_code,
            service_name=service_name,
            country=country,
            price_usd=price_usd,
            price_cup=price_cup,
            expires_at=expires_at
        )


class SMS(models.Model):
    """
    SMS message received for a phone rental.
    """
    
    phone_rental = models.ForeignKey(
        PhoneRental,
        on_delete=models.CASCADE,
        related_name='sms_messages',
        verbose_name='Alquiler'
    )
    code = models.CharField(
        'Código',
        max_length=50,
        help_text='Código de verificación extraído del SMS'
    )
    text = models.TextField(
        'Texto completo',
        blank=True,
        help_text='Texto completo del mensaje SMS'
    )
    daisy_message_id = models.IntegerField(
        'ID mensaje DaisySMS',
        null=True,
        blank=True,
        help_text='ID del mensaje en DaisySMS (si está disponible)'
    )
    received_at = models.DateTimeField(
        'Fecha de recepción',
        default=timezone.now
    )
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    
    class Meta:
        verbose_name = 'SMS'
        verbose_name_plural = 'SMS'
        ordering = ['-received_at']
    
    def __str__(self):
        return f'SMS para {self.phone_rental.phone_number}: {self.code}'
    
    @classmethod
    def create_from_daisy_response(cls, phone_rental, code: str, text: str = ''):
        """Create an SMS record from DaisySMS response."""
        sms = cls.objects.create(
            phone_rental=phone_rental,
            code=code,
            text=text
        )
        
        # Update rental status
        phone_rental.mark_sms_received()
        
        return sms
