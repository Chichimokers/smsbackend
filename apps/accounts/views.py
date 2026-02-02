"""
Views for Accounts app.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .models import UserAccount, ExchangeRate, Transaction
from .serializers import (
    UserAccountSerializer,
    TransactionSerializer,
    AddCreditSerializer,
    BalanceResponseSerializer,
    ExchangeRateSerializer
)

User = get_user_model()


class BalanceView(APIView):
    """View for getting user balance."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get current user's balance."""
        account, created = UserAccount.objects.get_or_create(user=request.user)
        
        data = {
            'balance_cup': account.balance_cup,
            'balance_usd': account.balance_usd,
            'exchange_rate': ExchangeRate.get_current_rate(),
            'currency': 'CUP'
        }
        
        serializer = BalanceResponseSerializer(data)
        return Response(serializer.data)


class TransactionListView(generics.ListAPIView):
    """View for listing user's transactions."""
    
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only the current user's transactions."""
        return Transaction.objects.filter(user=self.request.user)


class AddCreditView(APIView):
    """Admin view for adding credit to a user's account."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, user_id):
        """Add credit to a user's account."""
        serializer = AddCreditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get the target user
        target_user = get_object_or_404(User, id=user_id)
        
        # Get or create account
        account, created = UserAccount.objects.get_or_create(user=target_user)
        
        amount_cup = serializer.validated_data['amount_cup']
        reason = serializer.validated_data.get('reason', 'Crédito manual')
        
        # Store previous balance
        previous_balance = account.balance_cup
        
        # Add balance
        account.add_balance(amount_cup)
        
        # Create transaction record
        Transaction.create_manual_credit(
            user=target_user,
            amount_cup=amount_cup,
            description=reason,
            admin_user=request.user
        )
        
        return Response({
            'user_id': target_user.id,
            'user_email': target_user.email,
            'previous_balance_cup': str(previous_balance),
            'new_balance_cup': str(account.balance_cup),
            'amount_added_cup': str(amount_cup),
            'message': f'Crédito añadido exitosamente a {target_user.email}'
        }, status=status.HTTP_200_OK)


class ExchangeRateView(APIView):
    """View for getting/updating exchange rate."""
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
    
    def get(self, request):
        """Get current exchange rate."""
        rate = ExchangeRate.get_current_rate()
        latest = ExchangeRate.objects.first()
        
        data = {
            'rate_cup_per_usd': str(rate),
            'description': f'1 USD = {rate} CUP',
            'last_updated': latest.updated_at if latest else None
        }
        return Response(data)
    
    def post(self, request):
        """Create a new exchange rate (admin only)."""
        serializer = ExchangeRateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Tasa de cambio actualizada',
            'rate': serializer.data
        }, status=status.HTTP_201_CREATED)


class AdminTransactionListView(generics.ListAPIView):
    """Admin view for listing all transactions."""
    
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Transaction.objects.all()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by type
        transaction_type = self.request.query_params.get('type')
        if transaction_type:
            queryset = queryset.filter(type=transaction_type)
        
        return queryset
