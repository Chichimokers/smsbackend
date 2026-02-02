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
                'register': 'POST /api/users/register/',
                'login': 'POST /api/users/login/',
                'logout': 'POST /api/users/logout/',
                'refresh': 'POST /api/users/token/refresh/',
                'profile': 'GET /api/users/profile/',
            },
            'account': {
                'balance': 'GET /api/account/balance/',
                'transactions': 'GET /api/account/transactions/',
                'exchange_rate': 'GET /api/account/exchange-rate/',
            },
            'services': {
                'list': 'GET /api/services/',
            },
            'rentals': {
                'create': 'POST /api/rentals/',
                'list': 'GET /api/rentals/',
                'cancel': 'POST /api/rentals/<id>/cancel/',
            },
        }
    })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check
    path('health/', health_check, name='health-check'),
    
    # API root
    path('api/', api_root, name='api-root'),
    
    # App URLs
    path('api/users/', include('apps.users.urls')),
    path('api/account/', include('apps.accounts.urls')),
    path('api/services/', include('apps.services.urls')),
    path('api/rentals/', include('apps.rentals.urls')),
]

# Admin site customization
admin.site.site_header = 'SMS Rental Platform'
admin.site.site_title = 'SMS Rental Admin'
admin.site.index_title = 'Panel de Administración'
