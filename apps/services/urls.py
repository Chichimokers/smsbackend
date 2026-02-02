"""
URL configuration for Services app.
"""

from django.urls import path
from .views import ServiceListView, DaisyBalanceView

app_name = 'services'

urlpatterns = [
    # List all services
    path('', ServiceListView.as_view(), name='list'),
    
    # Admin: Check DaisySMS balance
    path('admin/daisy-balance/', DaisyBalanceView.as_view(), name='daisy-balance'),
]
