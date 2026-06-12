from rest_framework import serializers
from datetime import date
from django.utils.translation import gettext_lazy as _
from .models import UserPlant
from apps.plant_types.serializers import PlantTypeSerializer


class UserPlantSerializer(serializers.ModelSerializer):
    """Serializer для рослини користувача"""
    plant_type_details = PlantTypeSerializer(source='plant_type', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_until_watering = serializers.SerializerMethodField()
    days_until_fertilizing = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPlant
        fields = [
            'id', 'plant_type', 'plant_type_details',
            'custom_name', 'location', 'photo',
            'last_watered_date', 'last_fertilized_date', 'last_repotted_date',
            'next_watering_date', 'next_fertilizing_date', 'next_repotting_date',
            'status', 'status_display', 'has_sensor', 'notes',
            'days_until_watering', 'days_until_fertilizing',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'next_watering_date', 'next_fertilizing_date',
            'next_repotting_date', 'status', 'created_at', 'updated_at'
        ]
    
    def get_days_until_watering(self, obj):
        return (obj.next_watering_date - date.today()).days
    
    def get_days_until_fertilizing(self, obj):
        return (obj.next_fertilizing_date - date.today()).days
    
    def validate_last_watered_date(self, value):
        if value > date.today():
            raise serializers.ValidationError(
                _("Last watered date cannot be in the future")
            )
        return value

    def validate_last_fertilized_date(self, value):
        if value > date.today():
            raise serializers.ValidationError(
                _("Last fertilized date cannot be in the future")
            )
        return value

    def validate_last_repotted_date(self, value):
        if value and value > date.today():
            raise serializers.ValidationError(
                _("Last repotted date cannot be in the future")
            )
        return value
    
    def validate(self, attrs):
        user = self.context['request'].user
        
        if not self.instance:  
            if user.plant_limit is not None:
                current_count = UserPlant.objects.filter(user=user).count()
                if current_count >= user.plant_limit:
                    raise serializers.ValidationError(
                        _("You have reached the limit of plants for your account. "
                          "Upgrade to Premium for unlimited plants.")
                    )
        
        return attrs
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserPlantCreateSerializer(serializers.ModelSerializer):
    """Спрощений serializer для створення рослини"""
    
    class Meta:
        model = UserPlant
        fields = [
            'plant_type', 'custom_name', 'location', 'photo',
            'last_watered_date', 'last_fertilized_date',
            'last_repotted_date', 'notes'
        ]
    
    def validate_last_watered_date(self, value):
        if value > date.today():
            raise serializers.ValidationError(
                _("Last watered date cannot be in the future")
            )
        return value

    def validate_last_fertilized_date(self, value):
        if value > date.today():
            raise serializers.ValidationError(
                _("Last fertilized date cannot be in the future")
            )
        return value

    def validate_last_repotted_date(self, value):
        if value and value > date.today():
            raise serializers.ValidationError(
                _("Last repotted date cannot be in the future")
            )
        return value
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        plant = UserPlant.objects.create(**validated_data)
        
        from apps.plants.services import WateringScheduleService
        WateringScheduleService.create_care_tasks(plant)
        
        return plant