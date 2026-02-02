"""
URL configuration for Rentals app.

Simplified API with 3 endpoints:
- POST /api/rentals/ - Create rental
- GET /api/rentals/ - List all rentals with polling/sync
- POST /api/rentals/<id>/cancel/ - Cancel rental
"""

from django.urls import path
from .views import RentalView, CancelRentalView

app_name = 'rentals'

urlpatterns = [
    # POST: Create rental, GET: List all rentals with polling
    path('', RentalView.as_view(), name='rentals'),
    
    # Cancel rental
    path('<int:pk>/cancel/', CancelRentalView.as_view(), name='cancel'),
]
