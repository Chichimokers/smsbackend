"""
Views for Services app.
"""

import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import ExchangeRate
from .daisy_client import get_daisy_client, DaisySMSError
from .serializers import ServiceSerializer

logger = logging.getLogger(__name__)


class ServiceListView(APIView):
    """
    View for listing available services from DaisySMS.
    
    Calls DaisySMS API in real-time (with 5 minute cache).
    Returns services with prices in both USD and CUP.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get list of available services.
        
        Query params:
        - country: Filter by country code (e.g., '187' for USA)
        - service_code: Filter by service code (e.g., 'wa' for WhatsApp)
        - available: If 'true', only show services with available numbers
        """
        try:
            client = get_daisy_client()
            services = client.get_services(use_cache=True)
            
            # Apply filters
            country_filter = request.query_params.get('country')
            service_code_filter = request.query_params.get('service_code')
            available_only = request.query_params.get('available', '').lower() == 'true'
            
            if country_filter:
                services = [s for s in services if s.country == country_filter]
            
            if service_code_filter:
                services = [s for s in services if s.service_code == service_code_filter]
            
            if available_only:
                services = [s for s in services if s.available_numbers > 0]
            
            # Get exchange rate
            exchange_rate = ExchangeRate.get_current_rate()
            
            # Serialize services
            serializer = ServiceSerializer(services, many=True)
            
            return Response({
                'services': serializer.data,
                'exchange_rate': str(exchange_rate),
                'total': len(services)
            })
            
        except DaisySMSError as e:
            logger.error(f'DaisySMS API error: {e}')
            return Response(
                {'error': 'Error al obtener servicios de DaisySMS', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.exception(f'Unexpected error in ServiceListView: {e}')
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DaisyBalanceView(APIView):
    """
    Admin view for checking DaisySMS account balance.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get DaisySMS account balance (admin only for security)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Solo administradores pueden ver el balance de DaisySMS'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            client = get_daisy_client()
            balance = client.get_balance()
            
            return Response({
                'balance_usd': str(balance),
                'provider': 'DaisySMS'
            })
            
        except DaisySMSError as e:
            logger.error(f'DaisySMS API error: {e}')
            return Response(
                {'error': 'Error al obtener balance de DaisySMS', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
