"""
URL configuration for User app.
"""

from django.urls import path
from .views import UserProfileView, UserListView, UserDetailAdminView

app_name = 'users'

urlpatterns = [
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('admin/users/', UserListView.as_view(), name='admin-user-list'),
    path('admin/users/<int:pk>/', UserDetailAdminView.as_view(), name='admin-user-detail'),
]
