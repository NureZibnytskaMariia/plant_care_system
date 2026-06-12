from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer для реєстрації користувача"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm', 'language']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": _("Passwords don't match")})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer для логіну"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            username=attrs['email'],
            password=attrs['password']
        )
        
        if not user:
            raise serializers.ValidationError(_("Invalid credentials"))
        
        if not user.is_active:
            raise serializers.ValidationError(_("Account is disabled"))
        
        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer для профілю користувача"""
    is_premium_active = serializers.BooleanField(read_only=True)
    plant_limit = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'language',
            'is_premium', 'premium_start_date', 'premium_end_date',
            'is_premium_active', 'plant_limit', 'is_admin',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'email', 'is_premium', 'premium_start_date',
            'premium_end_date', 'is_admin', 'created_at', 'updated_at'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer для зміни пароля"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": _("Passwords don't match")})
        return attrs