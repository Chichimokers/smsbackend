"""
Admin configuration for User app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

from .email_service import send_verification_email

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model."""
    
    list_display = ['email', 'first_name', 'last_name', 'is_verified', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_verified', 'is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    actions = ['verify_users', 'resend_verification_email']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'google_id')}),
        ('Verificación de email', {'fields': ('is_verified', 'verification_token', 'verification_token_created_at')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    readonly_fields = ['verification_token', 'verification_token_created_at']
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'is_verified'),
        }),
    )
    
    @admin.action(description='Verificar usuarios seleccionados')
    def verify_users(self, request, queryset):
        """Mark selected users as verified."""
        count = queryset.filter(is_verified=False).update(is_verified=True)
        self.message_user(request, f'{count} usuario(s) verificado(s) exitosamente.')
    
    @admin.action(description='Reenviar email de verificación')
    def resend_verification_email(self, request, queryset):
        """Resend verification email to selected users."""
        sent_count = 0
        for user in queryset.filter(is_verified=False):
            if send_verification_email(user):
                sent_count += 1
        self.message_user(request, f'Email de verificación enviado a {sent_count} usuario(s).')
