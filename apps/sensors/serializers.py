from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import SensorData


class SensorDataSerializer(serializers.ModelSerializer):
    """Serializer для даних сенсорів"""
    plant_name = serializers.CharField(source='user_plant.custom_name', read_only=True)
    
    class Meta:
        model = SensorData
        fields = [
            'id', 'user_plant', 'plant_name',
            'temperature', 'soil_humidity', 'air_humidity', 'light_level',
            'recorded_at'
        ]
        read_only_fields = ['id', 'recorded_at']
    
    def validate_user_plant(self, value):
        """Перевірка що рослина належить користувачу"""
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError(_("This plant does not belong to you"))
        
        if not user.is_premium_active:
            raise serializers.ValidationError(
                _("Sensor data is only available for Premium users")
            )
        
        return value
    
    def validate_temperature(self, value):
        if value < -50 or value > 60:
            raise serializers.ValidationError(
                _("Temperature must be between -50°C and 60°C")
            )
        return value

    def validate_soil_humidity(self, value):
        # ЗМІНЕНО: soil_humidity тепер опціональний
        if value is not None:
            if value < 0 or value > 100:
                raise serializers.ValidationError(
                    _("Soil humidity must be between 0% and 100%")
                )
        return value
    
    # ДОДАНО: валідація вологості повітря
    def validate_air_humidity(self, value):
        if value is not None:
            if value < 0 or value > 100:
                raise serializers.ValidationError(
                    _("Air humidity must be between 0% and 100%")
                )
        return value

    def validate_light_level(self, value):
        if value < 0 or value > 200000:
            raise serializers.ValidationError(
                _("Light level must be between 0 and 200000 lux")
            )
        return value


class SensorDataChartSerializer(serializers.Serializer):
    """Serializer для відображення даних графіку"""
    temperature = serializers.DecimalField(max_digits=4, decimal_places=1)
    soil_humidity = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    air_humidity = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    light_level = serializers.IntegerField()
    recorded_at = serializers.DateTimeField()


# ДОДАНО: Serializer для призначення Arduino рослині
class AssignSensorSerializer(serializers.Serializer):
    """Serializer для призначення Arduino конкретній рослині"""
    plant_id = serializers.IntegerField(help_text=_("ID of the plant to assign Arduino sensor"))
    
    def validate_plant_id(self, value):
        """Перевірка що рослина існує і належить користувачу"""
        from apps.plants.models import UserPlant
        user = self.context['request'].user
        
        try:
            plant = UserPlant.objects.get(id=value, user=user)
        except UserPlant.DoesNotExist:
            raise serializers.ValidationError(_("Plant not found or does not belong to you"))
        
        if not user.is_premium_active:
            raise serializers.ValidationError(
                _("Sensor features are only available for Premium users")
            )
        
        return value