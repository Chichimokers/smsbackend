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
                'register': '/api/auth/registration/',
                'login': '/api/auth/login/',
                'logout': '/api/auth/logout/',
                'user': '/api/auth/user/',
                'google': '/api/auth/google/',
            },
            'account': {
                'balance': '/api/account/balance/',
                'transactions': '/api/account/transactions/',
                'exchange_rate': '/api/account/exchange-rate/',
            },
            'services': {
                'list': '/api/services/',
                'detail': '/api/services/<service_code>/',
            },
            'rentals': {
                'rent': '/api/rentals/',
                'list': '/api/rentals/list/',
                'detail': '/api/rentals/<id>/',
                'check_sms': '/api/rentals/<id>/check-sms/',
                'cancel': '/api/rentals/<id>/cancel/',
                'done': '/api/rentals/<id>/done/',
            },
            'admin': {
                'add_credit': '/api/account/admin/users/<user_id>/add-credit/',
                'users': '/api/users/admin/users/',
            }
        }
    })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check
    path('health/', health_check, name='health-check'),
    
    # API root
    path('api/', api_root, name='api-root'),
    
    # Authentication (dj-rest-auth)
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    
    # Social auth (Google)
    path('api/auth/', include('allauth.urls')),
    
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
