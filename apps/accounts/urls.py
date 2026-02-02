"""
URL configuration for Accounts app.
"""

from django.urls import path
from .views import (
    BalanceView,
    TransactionListView,
    AddCreditView,
    ExchangeRateView,
    AdminTransactionListView
)

app_name = 'accounts'

urlpatterns = [
    # User endpoints
    path('balance/', BalanceView.as_view(), name='balance'),
    path('transactions/', TransactionListView.as_view(), name='transactions'),
    
    # Exchange rate
    path('exchange-rate/', ExchangeRateView.as_view(), name='exchange-rate'),
    
    # Admin endpoints
    path('admin/users/<int:user_id>/add-credit/', AddCreditView.as_view(), name='add-credit'),
    path('admin/transactions/', AdminTransactionListView.as_view(), name='admin-transactions'),
]
