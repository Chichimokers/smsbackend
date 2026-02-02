"""
Main URL configuration for SMS Rental Platform.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    """Health check endpoint."""
    return JsonResponse({'status': 'ok', 'service': 'SMS Rental Platform'})


def api_root(request):
    """API root endpoint with available endpoints info."""
    return JsonResponse({
        'service': 'SMS Rental Platform API',
        'version': '1.0.0',
        'endpoints': {
            'auth': {
                'register': 'POST /api/v1/users/register/',
                'login': 'POST /api/v1/users/login/',
                'logout': 'POST /api/v1/users/logout/',
                'refresh': 'POST /api/v1/users/token/refresh/',
                'profile': 'GET /api/v1/users/profile/',
            },
            'account': {
                'balance': 'GET /api/v1/account/balance/',
                'transactions': 'GET /api/v1/account/transactions/',
                'exchange_rate': 'GET /api/v1/account/exchange-rate/',
            },
            'services': {
                'list': 'GET /api/v1/services/',
            },
            'rentals': {
                'create': 'POST /api/v1/rentals/',
                'list': 'GET /api/v1/rentals/',
                'cancel': 'POST /api/v1/rentals/<id>/cancel/',
            },
        }
    })


urlpatterns = [
    # Health check
    path('health/', health_check, name='health-check'),
    
    # API root
    path('api/', api_root, name='api-root'),
    
    # API v1 endpoints
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/account/', include('apps.accounts.urls')),
    path('api/v1/services/', include('apps.services.urls')),
    path('api/v1/rentals/', include('apps.rentals.urls')),
    
    # Django Admin (moved to v1 for consistency)
    path('api/v1/admin/', admin.site.urls),
    
    # Direct admin access (backward compatibility)
    path('admin/', admin.site.urls),
]

# Admin site customization
admin.site.site_header = 'SMS Rental Platform'
admin.site.site_title = 'SMS Rental Admin'
admin.site.index_title = 'Panel de Administración'
