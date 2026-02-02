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
    It verifies the account and shows an HTML response page.
    """
    
    permission_classes = [permissions.AllowAny]
    
    def _render_html(self, status_type: str, title: str, message: str, submessage: str = ''):
        """Render an HTML response page."""
        # Colors based on status
        colors = {
            'success': {'bg': '#10B981', 'icon': '✓'},
            'error': {'bg': '#EF4444', 'icon': '✗'},
            'warning': {'bg': '#F59E0B', 'icon': '!'},
        }
        color = colors.get(status_type, colors['error'])
        
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title} - SMS Rental</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}
                .card {{
                    background: white;
                    border-radius: 20px;
                    padding: 40px;
                    max-width: 450px;
                    width: 100%;
                    text-align: center;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                }}
                .icon {{
                    width: 80px;
                    height: 80px;
                    background: {color['bg']};
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 24px;
                    font-size: 40px;
                    color: white;
                }}
                h1 {{
                    color: #1f2937;
                    font-size: 24px;
                    margin-bottom: 12px;
                }}
                p {{
                    color: #6b7280;
                    font-size: 16px;
                    line-height: 1.6;
                    margin-bottom: 8px;
                }}
                .submessage {{
                    font-size: 14px;
                    color: #9ca3af;
                }}
                .logo {{
                    margin-bottom: 24px;
                    font-size: 28px;
                    font-weight: bold;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="logo">SMS Rental</div>
                <div class="icon">{color['icon']}</div>
                <h1>{title}</h1>
                <p>{message}</p>
                {f'<p class="submessage">{submessage}</p>' if submessage else ''}
            </div>
        </body>
        </html>
        """
        return html
    
    def get(self, request, token):
        from django.http import HttpResponse
        
        try:
            user = User.objects.get(verification_token=token)
        except User.DoesNotExist:
            html = self._render_html(
                'error',
                'Enlace inválido',
                'El enlace de verificación es inválido o ha expirado.',
                'Si necesitas un nuevo enlace, solicítalo desde la aplicación.'
            )
            return HttpResponse(html, content_type='text/html', status=400)
        
        if user.is_verified:
            html = self._render_html(
                'warning',
                'Ya verificado',
                'Tu cuenta ya estaba verificada.',
                'Puedes cerrar esta ventana e iniciar sesión.'
            )
            return HttpResponse(html, content_type='text/html')
        
        # Verify the user
        user.verify_email()
        logger.info(f'User {user.email} verified their email')
        
        html = self._render_html(
            'success',
            '¡Cuenta verificada!',
            'Tu email ha sido verificado exitosamente.',
            'Ya puedes cerrar esta ventana e iniciar sesión en la aplicación.'
        )
        return HttpResponse(html, content_type='text/html')


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
