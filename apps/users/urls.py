"""
URL configuration for User app.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, 
    LoginView, 
    LogoutView,
    VerifyEmailView,
    ResendVerificationView,
    UserProfileView, 
    UserListView, 
    UserDetailAdminView
)

app_name = 'users'

urlpatterns = [
    # Auth endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Email verification endpoints
    path('verify/<uuid:token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    
    # Profile endpoints
    path('profile/', UserProfileView.as_view(), name='profile'),
    
    # Admin endpoints
    path('admin/users/', UserListView.as_view(), name='admin-user-list'),
    path('admin/users/<int:pk>/', UserDetailAdminView.as_view(), name='admin-user-detail'),
]
