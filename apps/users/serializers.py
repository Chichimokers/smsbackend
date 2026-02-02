"""
Serializers for User app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for user details."""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'date_joined',
            'is_staff',
            'is_verified',
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'is_staff', 'is_verified']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class CustomRegisterSerializer(serializers.Serializer):
    """Custom registration serializer without username."""
    
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True, default='')
    last_name = serializers.CharField(required=False, allow_blank=True, default='')
    
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Ya existe un usuario con este email.')
        return value.lower()
    
    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Las contraseñas no coinciden.'})
        return data
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password1'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user
    
    def save(self, request=None):
        return self.create(self.validated_data)


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        email = data.get('email', '').lower()
        password = data.get('password', '')
        
        if not email or not password:
            raise serializers.ValidationError('Email y contraseña son requeridos.')
        
        user = authenticate(username=email, password=password)
        
        if not user:
            raise serializers.ValidationError('Credenciales inválidas.')
        
        if not user.is_active:
            raise serializers.ValidationError('Esta cuenta está desactivada.')
        
        data['user'] = user
        return data


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
