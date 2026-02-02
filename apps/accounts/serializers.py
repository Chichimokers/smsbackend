"""
Serializers for Accounts app.
"""

from rest_framework import serializers
from decimal import Decimal

from .models import UserAccount, ExchangeRate, Transaction


class ExchangeRateSerializer(serializers.ModelSerializer):
    """Serializer for ExchangeRate model."""
    
    class Meta:
        model = ExchangeRate
        fields = ['id', 'rate_cup_per_usd', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserAccountSerializer(serializers.ModelSerializer):
    """Serializer for UserAccount model."""
    
    balance_usd = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        read_only=True
    )
    exchange_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = UserAccount
        fields = ['balance_cup', 'balance_usd', 'exchange_rate', 'updated_at']
        read_only_fields = ['balance_cup', 'balance_usd', 'exchange_rate', 'updated_at']
    
    def get_exchange_rate(self, obj):
        return str(ExchangeRate.get_current_rate())


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model."""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    rental_phone = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'type',
            'type_display',
            'amount_usd',
            'amount_cup',
            'balance_after_cup',
            'description',
            'rental_phone',
            'created_at'
        ]
        read_only_fields = fields
    
    def get_rental_phone(self, obj):
        if obj.related_rental:
            return obj.related_rental.phone_number
        return None


class AddCreditSerializer(serializers.Serializer):
    """Serializer for adding credit to a user account (admin only)."""
    
    amount_cup = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        help_text='Cantidad de CUP a agregar'
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        default='Crédito manual',
        help_text='Razón del crédito'
    )


class BalanceResponseSerializer(serializers.Serializer):
    """Serializer for balance response."""
    
    balance_cup = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_usd = serializers.DecimalField(max_digits=10, decimal_places=4)
    exchange_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(default='CUP')
