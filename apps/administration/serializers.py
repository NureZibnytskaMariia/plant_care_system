from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.users.models import User


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer для управління користувачами (адмін)"""
    is_premium_active = serializers.BooleanField(read_only=True)
    total_plants = serializers.SerializerMethodField()
    
    password = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
        help_text=_("Password for new user (required when creating)")
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
        help_text=_("Confirm password")
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'language',
            'is_premium', 'is_premium_active',
            'premium_start_date', 'premium_end_date',
            'is_admin', 'is_active', 'total_plants',
            'created_at', 'updated_at',
            'password', 'password_confirm'  
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_plants(self, obj):
        return obj.plants.count()
    
    def validate(self, attrs):
        """Валідація при створенні та оновленні"""
        if not self.instance:  
            if 'password' not in attrs or not attrs['password']:
                raise serializers.ValidationError({
                    'password': _("Password is required when creating a new user")
                })
            
            if 'password_confirm' not in attrs or not attrs['password_confirm']:
                raise serializers.ValidationError({
                    'password_confirm': _("Password confirmation is required")
                })
            
            if attrs['password'] != attrs['password_confirm']:
                raise serializers.ValidationError({
                    'password_confirm': _("Passwords do not match")
                })
            
            if len(attrs['password']) < 8:
                raise serializers.ValidationError({
                    'password': _("Password must be at least 8 characters long")
                })
        
        else: 
            if 'password' in attrs:
                if 'password_confirm' not in attrs:
                    raise serializers.ValidationError({
                        'password_confirm': _("Password confirmation is required when changing password")
                    })
                
                if attrs['password'] != attrs['password_confirm']:
                    raise serializers.ValidationError({
                        'password_confirm': _("Passwords do not match")
                    })
                
                if len(attrs['password']) < 8:
                    raise serializers.ValidationError({
                        'password': _("Password must be at least 8 characters long")
                    })
        
        return attrs
    
    def create(self, validated_data):
        """Створення користувача з паролем"""
        validated_data.pop('password_confirm', None)
        
        password = validated_data.pop('password')
        
        user = User.objects.create(**validated_data)
        
        user.set_password(password)
        user.save()
        
        return user
    
    def update(self, instance, validated_data):
        """Оновлення користувача"""
        validated_data.pop('password_confirm', None)
        
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class GrantPremiumSerializer(serializers.Serializer):
    """Serializer для надання Premium"""
    days = serializers.IntegerField(min_value=1, default=30)
    
    def validate_days(self, value):
        if value > 3650: 
            raise serializers.ValidationError(_("Maximum 3650 days (10 years)"))
        return value


class SystemStatisticsSerializer(serializers.Serializer):
    """Serializer для відображення статистики системи"""
    total_users = serializers.IntegerField()
    premium_users = serializers.IntegerField()
    free_users = serializers.IntegerField()
    total_plants = serializers.IntegerField()
    plant_statuses = serializers.DictField()
    users_with_sensors = serializers.IntegerField()