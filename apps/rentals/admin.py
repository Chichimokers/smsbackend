"""
Admin configuration for Rentals app.
"""

from django.contrib import admin
from .models import PhoneRental, SMS


class SMSInline(admin.TabularInline):
    """Inline for SMS messages in rental."""
    
    model = SMS
    extra = 0
    readonly_fields = ['code', 'text', 'received_at', 'created_at']
    can_delete = False


@admin.register(PhoneRental)
class PhoneRentalAdmin(admin.ModelAdmin):
    """Admin for PhoneRental model."""
    
    list_display = [
        'phone_number',
        'user',
        'service_name',
        'status',
        'price_cup',
        'refunded',
        'rented_at',
        'expires_at'
    ]
    list_filter = ['status', 'service_code', 'refunded', 'rented_at']
    search_fields = ['phone_number', 'user__email', 'daisy_rental_id']
    readonly_fields = [
        'daisy_rental_id',
        'phone_number',
        'service_code',
        'service_name',
        'price_usd',
        'price_cup',
        'rented_at',
        'expires_at',
        'last_polled_at',
        'created_at',
        'updated_at'
    ]
    date_hierarchy = 'rented_at'
    inlines = [SMSInline]
    
    def has_add_permission(self, request):
        # Rentals should be created through API only
        return False


@admin.register(SMS)
class SMSAdmin(admin.ModelAdmin):
    """Admin for SMS model."""
    
    list_display = ['phone_rental', 'code', 'received_at']
    list_filter = ['received_at']
    search_fields = ['code', 'text', 'phone_rental__phone_number']
    readonly_fields = ['phone_rental', 'code', 'text', 'daisy_message_id', 'received_at', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
