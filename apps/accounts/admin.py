"""
Admin configuration for Accounts app.
"""

from django.contrib import admin
from .models import UserAccount, ExchangeRate, Transaction


@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    """Admin for UserAccount model."""
    
    list_display = ['user', 'balance_cup', 'balance_usd', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def balance_usd(self, obj):
        return f'${obj.balance_usd:.4f}'
    balance_usd.short_description = 'Saldo USD'


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    """Admin for ExchangeRate model."""
    
    list_display = ['rate_cup_per_usd', 'notes', 'created_at', 'updated_at']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin for Transaction model."""
    
    list_display = ['user', 'type', 'amount_cup', 'amount_usd', 'balance_after_cup', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['user__email', 'description']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def has_change_permission(self, request, obj=None):
        # Transactions should not be editable
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Transactions should not be deletable
        return False
