"""
URL configuration for Rentals app.

Simplified API with 3 endpoints:
- POST /api/rentals/ - Create rental
- GET /api/rentals/ - List all rentals with polling/sync
- POST /api/rentals/<id>/cancel/ - Cancel rental
"""

from django.urls import path
from .views import RentNumberView, RentalListView, CancelRentalView

app_name = 'rentals'

urlpatterns = [
    # POST: Create rental, GET: List all rentals with polling
    path('', RentNumberView.as_view(), name='rent'),
    path('', RentalListView.as_view(), name='list'),
    
    # Cancel rental
    path('<int:pk>/cancel/', CancelRentalView.as_view(), name='cancel'),
]
