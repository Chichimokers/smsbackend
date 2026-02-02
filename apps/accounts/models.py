"""
Models for Accounts app - UserAccount, ExchangeRate, Transaction.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


class ExchangeRate(models.Model):
    """
    Exchange rate for USD to CUP conversion.
    Only the latest record is used for calculations.
    Admin can update this to change the conversion rate.
    """
    
    rate_cup_per_usd = models.DecimalField(
        'Tasa CUP por USD',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Ejemplo: 4800 significa que 1 USD = 4800 CUP'
    )
    notes = models.TextField('Notas', blank=True)
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Tasa de cambio'
        verbose_name_plural = 'Tasas de cambio'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'1 USD = {self.rate_cup_per_usd} CUP'
    
    @classmethod
    def get_current_rate(cls):
        """Get the current (latest) exchange rate."""
        rate = cls.objects.first()
        if rate:
            return rate.rate_cup_per_usd
        # Return default from settings if no rate exists
        return Decimal(str(settings.DEFAULT_EXCHANGE_RATE_CUP_PER_USD))
    
    @classmethod
    def usd_to_cup(cls, usd_amount):
        """Convert USD to CUP using current rate."""
        rate = cls.get_current_rate()
        return Decimal(str(usd_amount)) * rate
    
    @classmethod
    def cup_to_usd(cls, cup_amount):
        """Convert CUP to USD using current rate."""
        rate = cls.get_current_rate()
        if rate == 0:
            return Decimal('0')
        return Decimal(str(cup_amount)) / rate


class UserAccount(models.Model):
    """
    User account for managing balance/credit.
    Each user has one account that tracks their CUP balance.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='account',
        verbose_name='Usuario'
    )
    balance_cup = models.DecimalField(
        'Saldo CUP',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Saldo actual en pesos cubanos'
    )
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Cuenta de usuario'
        verbose_name_plural = 'Cuentas de usuarios'
    
    def __str__(self):
        return f'{self.user.email} - {self.balance_cup} CUP'
    
    @property
    def balance_usd(self):
        """Get balance converted to USD."""
        return ExchangeRate.cup_to_usd(self.balance_cup)
    
    def has_sufficient_balance_cup(self, amount_cup):
        """Check if user has enough balance in CUP."""
        return self.balance_cup >= Decimal(str(amount_cup))
    
    def has_sufficient_balance_usd(self, amount_usd):
        """Check if user has enough balance in USD equivalent."""
        amount_cup = ExchangeRate.usd_to_cup(amount_usd)
        return self.has_sufficient_balance_cup(amount_cup)
    
    def deduct_balance(self, amount_cup, description=''):
        """
        Deduct balance from account.
        Returns True if successful, False if insufficient funds.
        """
        amount_cup = Decimal(str(amount_cup))
        if not self.has_sufficient_balance_cup(amount_cup):
            return False
        self.balance_cup -= amount_cup
        self.save()
        return True
    
    def add_balance(self, amount_cup):
        """Add balance to account."""
        amount_cup = Decimal(str(amount_cup))
        self.balance_cup += amount_cup
        self.save()
        return True


class Transaction(models.Model):
    """
    Transaction history for user accounts.
    Tracks all balance changes: rentals, refunds, manual credits.
    """
    
    class TransactionType(models.TextChoices):
        RENT = 'RENT', 'Alquiler de número'
        REFUND = 'REFUND', 'Reembolso'
        MANUAL_CREDIT = 'MANUAL_CREDIT', 'Crédito manual'
        MANUAL_DEBIT = 'MANUAL_DEBIT', 'Débito manual'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Usuario'
    )
    type = models.CharField(
        'Tipo',
        max_length=20,
        choices=TransactionType.choices
    )
    amount_usd = models.DecimalField(
        'Monto USD',
        max_digits=10,
        decimal_places=4,
        help_text='Monto en USD (puede ser negativo para débitos)'
    )
    amount_cup = models.DecimalField(
        'Monto CUP',
        max_digits=12,
        decimal_places=2,
        help_text='Monto en CUP (puede ser negativo para débitos)'
    )
    balance_after_cup = models.DecimalField(
        'Saldo después CUP',
        max_digits=12,
        decimal_places=2,
        help_text='Saldo de la cuenta después de esta transacción'
    )
    description = models.CharField('Descripción', max_length=500)
    related_rental = models.ForeignKey(
        'rentals.PhoneRental',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Alquiler relacionado'
    )
    created_at = models.DateTimeField('Fecha', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-created_at']
    
    def __str__(self):
        sign = '+' if self.amount_cup > 0 else ''
        return f'{self.user.email}: {sign}{self.amount_cup} CUP ({self.get_type_display()})'
    
    @classmethod
    def create_rental_transaction(cls, user, amount_usd, amount_cup, rental, description=''):
        """Create a transaction for a rental (debit)."""
        account = user.account
        return cls.objects.create(
            user=user,
            type=cls.TransactionType.RENT,
            amount_usd=-abs(Decimal(str(amount_usd))),
            amount_cup=-abs(Decimal(str(amount_cup))),
            balance_after_cup=account.balance_cup,
            description=description or f'Alquiler: {rental.phone_number}',
            related_rental=rental
        )
    
    @classmethod
    def create_refund_transaction(cls, user, amount_usd, amount_cup, rental, description=''):
        """Create a transaction for a refund (credit)."""
        account = user.account
        return cls.objects.create(
            user=user,
            type=cls.TransactionType.REFUND,
            amount_usd=abs(Decimal(str(amount_usd))),
            amount_cup=abs(Decimal(str(amount_cup))),
            balance_after_cup=account.balance_cup,
            description=description or f'Reembolso: {rental.phone_number}',
            related_rental=rental
        )
    
    @classmethod
    def create_manual_credit(cls, user, amount_cup, description='', admin_user=None):
        """Create a transaction for manual credit by admin."""
        account = user.account
        amount_usd = ExchangeRate.cup_to_usd(amount_cup)
        admin_info = f' por {admin_user.email}' if admin_user else ''
        return cls.objects.create(
            user=user,
            type=cls.TransactionType.MANUAL_CREDIT,
            amount_usd=abs(Decimal(str(amount_usd))),
            amount_cup=abs(Decimal(str(amount_cup))),
            balance_after_cup=account.balance_cup,
            description=description or f'Crédito manual{admin_info}'
        )
