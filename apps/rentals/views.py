"""
Views for Rentals app.
Simplified API with only 3 endpoints:
- POST /api/rentals/ - Create rental
- GET /api/rentals/ - List all rentals with polling/sync
- POST /api/rentals/<id>/cancel/ - Cancel rental
"""

import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import UserAccount, ExchangeRate, Transaction
from apps.services.daisy_client import (
    get_daisy_client,
    DaisySMSError,
    NoNumbersAvailableError,
    InsufficientBalanceError,
    MaxPriceExceededError,
    TooManyActiveRentalsError,
    RentalNotFoundError,
    RentalStatus
)
from .models import PhoneRental, SMS
from .serializers import RentNumberSerializer, SMSSerializer

logger = logging.getLogger(__name__)

# Maximum active rentals per user
MAX_ACTIVE_RENTALS = 5


class RentalView(APIView):
    """
    Main rental endpoint.
    
    POST /api/rentals/ - Create a new phone rental
    GET /api/rentals/ - List all rentals with live sync from DaisySMS
    
    POST:
    - Validates user has less than MAX_ACTIVE_RENTALS active
    - Validates user balance
    - Calls DaisySMS to rent number
    - Deducts balance
    - Creates rental record
    
    GET:
    - Lists all rentals from DB for the user
    - For ACTIVE rentals, syncs with DaisySMS to check SMS status
    - Automatically processes refunds for expired rentals without SMS
    - Returns complete info including remaining time, SMS codes, refund status
    
    Query params (GET):
    - status: Filter by status (ACTIVE, SMS_RECEIVED, REFUNDED, CANCELLED, all)
    - limit: Number of results (default 50)
    - offset: Pagination offset (default 0)
    """
    
    permission_classes = [IsAuthenticated]
    
    def _process_refund(self, rental, account):
        """
        Process automatic refund for expired rental without SMS.
        Returns the refund amount in CUP.
        """
        account.add_balance(rental.price_cup)
        
        # Create refund transaction
        Transaction.create_refund_transaction(
            user=rental.user,
            amount_usd=rental.price_usd,
            amount_cup=rental.price_cup,
            rental=rental,
            description=f'Reembolso automático: {rental.formatted_phone} (expirado sin SMS)'
        )
        
        # Try to cancel in DaisySMS (might already be cancelled)
        try:
            client = get_daisy_client()
            client.cancel_rental(rental.daisy_rental_id)
        except DaisySMSError as e:
            logger.warning(f'Could not cancel rental {rental.id} in DaisySMS: {e}')
        
        # Mark as refunded
        rental.mark_refunded()
        
        logger.info(f'Rental {rental.id} expired and refunded: {rental.price_cup} CUP')
        
        return rental.price_cup
    
    def _sync_rental_with_daisy(self, rental, client, account):
        """
        Sync a single rental with DaisySMS.
        Returns updated rental data dict.
        """
        refund_info = None
        
        # Only sync if ACTIVE (not already processed)
        if rental.status == PhoneRental.RentalStatus.ACTIVE:
            logger.info(f'[Polling] Rental {rental.id} is ACTIVE, calling getStatus for daisy_rental_id={rental.daisy_rental_id}')
            try:
                result = client.get_sms_status(rental.daisy_rental_id)
                
                if result.status == RentalStatus.OK and result.code:
                    # SMS received!
                    if not rental.sms_messages.exists():
                        SMS.create_from_daisy_response(
                            phone_rental=rental,
                            code=result.code,
                            text=result.text or ''
                        )
                        logger.info(f'SMS received for rental {rental.id}: {result.code}')
                
                elif result.status == RentalStatus.CANCEL:
                    # Rental was cancelled by DaisySMS
                    rental.mark_cancelled()
                    
            except RentalNotFoundError:
                # Rental not found in DaisySMS, mark as cancelled
                logger.warning(f'Rental {rental.id} not found in DaisySMS')
                rental.mark_cancelled()
                
            except DaisySMSError as e:
                logger.warning(f'DaisySMS error syncing rental {rental.id}: {e}')
            
            # Check if expired and needs refund
            if rental.status == PhoneRental.RentalStatus.ACTIVE and rental.is_expired:
                if not rental.sms_messages.exists():
                    # Expired without SMS - process refund
                    refund_amount = self._process_refund(rental, account)
                    refund_info = {
                        'refund_amount_cup': str(refund_amount),
                        'new_balance_cup': str(account.balance_cup)
                    }
                else:
                    # Expired but has SMS - just mark expired (no refund)
                    rental.mark_expired()
        else:
            logger.info(f'[Polling] Rental {rental.id} skipped - status is {rental.status} (not ACTIVE)')
        
        # Build rental data dict
        sms_messages = rental.sms_messages.all()
        rental_data = {
            'id': rental.id,
            'daisy_rental_id': rental.daisy_rental_id,
            'phone': rental.formatted_phone,
            'service_code': rental.service_code,
            'service_name': rental.service_name,
            'status': rental.status,
            'status_display': rental.get_status_display(),
            'price_cup': str(rental.price_cup),
            'price_usd': str(rental.price_usd),
            'rented_at': rental.rented_at,
            'expires_at': rental.expires_at,
            'remaining_time_seconds': rental.remaining_time_seconds,
            'has_sms': sms_messages.exists(),
            'sms': SMSSerializer(sms_messages, many=True).data,
            'refunded': rental.refunded,
        }
        
        # Add refund info if applicable
        if refund_info:
            rental_data.update(refund_info)
        elif rental.refunded:
            rental_data['refund_amount_cup'] = str(rental.price_cup)
        
        return rental_data
    
    @transaction.atomic
    def get(self, request):
        """List all rentals with live sync from DaisySMS."""
        user = request.user
        
        # Get user account (with lock for potential refunds)
        account, _ = UserAccount.objects.select_for_update().get_or_create(user=user)
        
        # Get query params
        status_filter = request.query_params.get('status', '').upper()
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        # Base queryset
        queryset = PhoneRental.objects.filter(user=user).select_for_update()
        
        # Apply status filter
        if status_filter and status_filter != 'ALL':
            queryset = queryset.filter(status=status_filter)
        
        # Order by most recent first
        queryset = queryset.order_by('-created_at')
        
        # Get total before pagination
        total = queryset.count()
        
        # Apply pagination
        rentals = list(queryset[offset:offset + limit])
        
        # Get DaisySMS client (only if we have active rentals to sync)
        has_active = any(r.status == PhoneRental.RentalStatus.ACTIVE for r in rentals)
        client = get_daisy_client() if has_active else None
        
        # Sync each rental and build response
        rentals_data = []
        for rental in rentals:
            rental_data = self._sync_rental_with_daisy(rental, client, account)
            rentals_data.append(rental_data)
        
        return Response({
            'rentals': rentals_data,
            'balance_cup': str(account.balance_cup),
            'total': total,
            'limit': limit,
            'offset': offset
        })
    
    @transaction.atomic
    def post(self, request):
        """Rent a phone number for a service."""
        serializer = RentNumberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service_code = serializer.validated_data['service_code']
        max_price_usd = serializer.validated_data.get('max_price_usd')
        country = serializer.validated_data.get('country', '187')
        areas = serializer.validated_data.get('areas') or None
        carriers = serializer.validated_data.get('carriers') or None
        number = serializer.validated_data.get('number') or None
        
        # Get user account
        account, _ = UserAccount.objects.select_for_update().get_or_create(
            user=request.user
        )
        
        # Check active rentals limit
        active_count = PhoneRental.objects.filter(
            user=request.user,
            status=PhoneRental.RentalStatus.ACTIVE
        ).count()
        
        if active_count >= MAX_ACTIVE_RENTALS:
            return Response(
                {
                    'error': f'Máximo {MAX_ACTIVE_RENTALS} alquileres activos permitidos',
                    'active_rentals': active_count,
                    'message': 'Espera a que expiren o cancela algunos para crear nuevos'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get service info to check price
            client = get_daisy_client()
            services = client.get_services(use_cache=True)
            
            # Find the service in the specified country
            service = None
            available_countries = []
            for s in services:
                if s.service_code == service_code:
                    available_countries.append(s.country)
                    if s.country == country:
                        service = s
                        break
            
            if not service:
                if available_countries:
                    return Response(
                        {
                            'error': f'Servicio {service_code} no disponible en el pais {country}',
                            'available_countries': list(set(available_countries)),
                            'hint': 'Use GET /api/services/?service_code={} para ver paises disponibles'.format(service_code)
                        },
                        status=status.HTTP_404_NOT_FOUND
                    )
                else:
                    return Response(
                        {'error': f'Servicio {service_code} no encontrado'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # Calculate price in CUP
            estimated_price_cup = ExchangeRate.usd_to_cup(service.price_usd)
            
            # Check user balance
            if not account.has_sufficient_balance_cup(estimated_price_cup):
                return Response(
                    {
                        'error': 'Saldo insuficiente',
                        'required_cup': str(estimated_price_cup),
                        'available_cup': str(account.balance_cup)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Rent from DaisySMS with optional parameters
            # Note: DaisySMS API doesn't accept country param, country is implicit from service selection
            rental_result = client.rent_number(
                service_code=service_code,
                max_price_usd=max_price_usd,
                areas=areas,
                carriers=carriers,
                number=number
            )
            
            # Calculate actual price in CUP (from actual DaisySMS price)
            actual_price_cup = ExchangeRate.usd_to_cup(rental_result.price_usd)
            
            # Deduct balance
            if not account.deduct_balance(actual_price_cup):
                # This shouldn't happen but just in case
                # Try to cancel the rental
                try:
                    client.cancel_rental(rental_result.rental_id)
                except Exception:
                    pass
                return Response(
                    {'error': 'Error al procesar el pago'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Create rental record
            rental = PhoneRental.create_rental(
                user=request.user,
                daisy_rental_id=rental_result.rental_id,
                phone_number=rental_result.phone_number,
                service_code=service_code,
                service_name=service.name,
                price_usd=rental_result.price_usd,
                price_cup=actual_price_cup,
                country=country
            )
            
            # Create transaction record
            Transaction.create_rental_transaction(
                user=request.user,
                amount_usd=rental_result.price_usd,
                amount_cup=actual_price_cup,
                rental=rental,
                description=f'Alquiler {service.name}: {rental.formatted_phone}'
            )
            
            # Build response with requested options
            response_data = {
                'id': rental.id,
                'daisy_rental_id': rental.daisy_rental_id,
                'phone': rental.formatted_phone,
                'service_code': rental.service_code,
                'service_name': rental.service_name,
                'status': rental.status,
                'status_display': rental.get_status_display(),
                'price_usd': str(rental.price_usd),
                'price_cup': str(rental.price_cup),
                'rented_at': rental.rented_at,
                'expires_at': rental.expires_at,
                'remaining_time_seconds': rental.remaining_time_seconds,
                'has_sms': False,
                'sms': [],
                'refunded': False,
                'new_balance_cup': str(account.balance_cup),
            }
            
            # Add requested options if provided
            if areas:
                response_data['requested_areas'] = areas
                response_data['price_markup_note'] = 'Área específica: +20% al precio'
            if carriers:
                response_data['requested_carrier'] = carriers
                response_data['price_markup_note'] = 'Carrier específico: +20% al precio'
            if number:
                response_data['requested_number'] = number
                response_data['price_markup_note'] = 'Número específico: +20% al precio'
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except NoNumbersAvailableError:
            return Response(
                {'error': f'No hay números disponibles para {service_code}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except InsufficientBalanceError:
            return Response(
                {'error': 'Saldo insuficiente en la cuenta de DaisySMS'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except MaxPriceExceededError:
            return Response(
                {'error': 'El precio excede el máximo especificado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except TooManyActiveRentalsError:
            return Response(
                {'error': 'Demasiados alquileres activos en DaisySMS'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except DaisySMSError as e:
            logger.error(f'DaisySMS error: {e}')
            return Response(
                {'error': 'Error al comunicarse con DaisySMS', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class CancelRentalView(APIView):
    """
    Cancel an active rental and get refund.
    
    POST /api/rentals/<id>/cancel/
    
    - Only works if rental is ACTIVE and has no SMS received
    - Calls DaisySMS to cancel
    - Refunds user balance
    """
    
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, pk):
        """Cancel a rental."""
        rental = get_object_or_404(
            PhoneRental.objects.select_for_update(),
            pk=pk,
            user=request.user
        )
        
        # Check if can be cancelled
        if rental.status != PhoneRental.RentalStatus.ACTIVE:
            return Response(
                {
                    'error': 'Este alquiler no puede ser cancelado',
                    'current_status': rental.status,
                    'status_display': rental.get_status_display()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if SMS was already received
        if rental.sms_messages.exists():
            return Response(
                {'error': 'No se puede cancelar un alquiler con SMS recibido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user account
        account, _ = UserAccount.objects.select_for_update().get_or_create(
            user=request.user
        )
        
        try:
            # Cancel in DaisySMS
            client = get_daisy_client()
            client.cancel_rental(rental.daisy_rental_id)
            
        except RentalNotFoundError:
            # Rental not found in DaisySMS, might be already cancelled/expired
            # Still proceed with refund
            logger.warning(f'Rental {rental.id} not found in DaisySMS during cancel')
            
        except DaisySMSError as e:
            logger.error(f'DaisySMS error cancelling rental: {e}')
            return Response(
                {'error': 'Error al cancelar en DaisySMS', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Refund to user
        account.add_balance(rental.price_cup)
        
        # Create refund transaction
        Transaction.create_refund_transaction(
            user=request.user,
            amount_usd=rental.price_usd,
            amount_cup=rental.price_cup,
            rental=rental,
            description=f'Cancelación: {rental.formatted_phone}'
        )
        
        # Mark as refunded
        rental.mark_refunded()
        
        return Response({
            'rental_id': rental.id,
            'status': rental.status,
            'status_display': rental.get_status_display(),
            'refunded': True,
            'refund_amount_cup': str(rental.price_cup),
            'new_balance_cup': str(account.balance_cup),
            'message': 'Alquiler cancelado y reembolsado exitosamente'
        })
