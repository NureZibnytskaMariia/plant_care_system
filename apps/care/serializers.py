from rest_framework import serializers
from datetime import date
from .models import CareLog


class CareLogSerializer(serializers.ModelSerializer):
    """Serializer для завдань догляду"""
    plant_name = serializers.CharField(source='user_plant.custom_name', read_only=True)
    plant_location = serializers.CharField(source='user_plant.location', read_only=True)
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = CareLog
        fields = [
            'id', 'user_plant', 'plant_name', 'plant_location',
            'scheduled_date', 'task_type', 'task_type_display',
            'is_completed', 'completed_at', 'skipped',
            'auto_adjusted', 'notes', 'is_overdue',
            'created_at'
        ]
        read_only_fields = [
            'id', 'completed_at', 'auto_adjusted', 'created_at'
        ]
    
    def get_is_overdue(self, obj):
        return obj.scheduled_date < date.today() and not obj.is_completed


class CompleteCareTaskSerializer(serializers.Serializer):
    """Serializer для відмітки виконання завдання"""
    notes = serializers.CharField(required=False, allow_blank=True)