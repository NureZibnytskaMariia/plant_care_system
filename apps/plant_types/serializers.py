from rest_framework import serializers
from .models import PlantType


class PlantTypeSerializer(serializers.ModelSerializer):
    """Serializer для типу рослини"""
    # Динамічне поле назви залежно від мови користувача
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    care_tips = serializers.SerializerMethodField()
    is_custom = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PlantType
        fields = [
            'id', 'name', 'name_uk', 'name_en', 'scientific_name',
            'watering_frequency_days', 'fertilizing_frequency_days',
            'repotting_frequency_months',
            'optimal_temp_min', 'optimal_temp_max',
            'optimal_humidity_min', 'optimal_humidity_max',
            'optimal_light_min', 'optimal_light_max',
            'description', 'care_tips', 'is_custom',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_name(self, obj):
        request = self.context.get('request')
        if request and hasattr(request.user, 'language'):
            lang = request.user.language
        else:
            lang = 'en'
        return obj.name_uk if lang == 'uk' else obj.name_en
    
    def get_description(self, obj):
        request = self.context.get('request')
        if request and hasattr(request.user, 'language'):
            lang = request.user.language
        else:
            lang = 'en'
        return obj.description_uk if lang == 'uk' else obj.description_en
    
    def get_care_tips(self, obj):
        request = self.context.get('request')
        if request and hasattr(request.user, 'language'):
            lang = request.user.language
        else:
            lang = 'en'
        return obj.care_tips_uk if lang == 'uk' else obj.care_tips_en


class PlantTypeCreateSerializer(serializers.ModelSerializer):
    """Serializer для створення custom рослин користувачами"""
    
    class Meta:
        model = PlantType
        fields = [
            'name_uk', 'name_en', 'scientific_name',
            'watering_frequency_days', 'fertilizing_frequency_days',
            'repotting_frequency_months',
            'optimal_temp_min', 'optimal_temp_max',
            'optimal_humidity_min', 'optimal_humidity_max',
            'optimal_light_min', 'optimal_light_max',
            'description_uk', 'description_en',
            'care_tips_uk', 'care_tips_en'
        ]
    
    def create(self, validated_data):
        validated_data['created_by_user'] = self.context['request'].user
        return super().create(validated_data)