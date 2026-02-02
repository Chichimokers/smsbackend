"""
Views for User app.
"""

import logging
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.conf import settings

from .serializers import UserDetailSerializer, UserUpdateSerializer, CustomRegisterSerializer, LoginSerializer
from .email_service import send_verification_email, send_resend_verification_email

logger = logging.getLogger(__name__)
User = get_user_model()


class RegisterView(APIView):
    """User registration view with email verification."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = CustomRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send verification email
        email_sent = send_verification_email(user)
        
        if email_sent:
            logger.info(f'User {user.email} registered, verification email sent')
        else:
            logger.warning(f'User {user.email} registered, but verification email failed to send')
        
        # Don't return tokens - user needs to verify email first
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'email_sent': email_sent,
            'message': 'Registro exitoso. Por favor revisa tu email para verificar tu cuenta.'
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """User login view - requires email verification."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Check if user is verified
        if not user.is_verified:
            return Response({
                'error': 'Email no verificado',
                'message': 'Por favor verifica tu email antes de iniciar sesión.',
                'can_resend': True
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserDetailSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Login exitoso'
        })


class VerifyEmailView(APIView):
    """
    Verify user email via token.
    GET /api/auth/verify/<uuid:token>/
    
    This endpoint is called when user clicks the link in their email.
    It verifies the account and redirects to frontend.
    """
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        try:
            user = User.objects.get(verification_token=token)
        except User.DoesNotExist:
            # Redirect to frontend with error
            frontend_url = settings.FRONTEND_URL.rstrip('/')
            return redirect(f'{frontend_url}/verify-email?status=invalid')
        
        if user.is_verified:
            # Already verified - redirect to frontend
            frontend_url = settings.FRONTEND_URL.rstrip('/')
            return redirect(f'{frontend_url}/verify-email?status=already_verified')
        
        # Verify the user
        user.verify_email()
        logger.info(f'User {user.email} verified their email')
        
        # Redirect to frontend with success
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        return redirect(f'{frontend_url}/verify-email?status=success')


class ResendVerificationView(APIView):
    """
    Resend verification email.
    POST /api/auth/resend-verification/
    
    Body: { "email": "user@example.com" }
    """
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email', '').lower().strip()
        
        if not email:
            return Response({
                'error': 'Email requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if user exists or not
            return Response({
                'message': 'Si el email existe en nuestro sistema, recibirás un correo de verificación.'
            })
        
        if user.is_verified:
            return Response({
                'message': 'Este email ya está verificado. Puedes iniciar sesión.'
            })
        
        # Resend verification email
        email_sent = send_resend_verification_email(user)
        
        if email_sent:
            logger.info(f'Resent verification email to {user.email}')
        
        return Response({
            'message': 'Si el email existe en nuestro sistema, recibirás un correo de verificación.'
        })


class LogoutView(APIView):
    """User logout view - blacklists refresh token."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logout exitoso'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'message': 'Logout exitoso'}, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating the authenticated user's profile."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserDetailSerializer
    
    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    """Admin view for listing all users."""
    
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        email = self.request.query_params.get('email')
        if email:
            queryset = queryset.filter(email__icontains=email)
        return queryset


class UserDetailAdminView(generics.RetrieveAPIView):
    """Admin view for retrieving a specific user."""
    
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()
