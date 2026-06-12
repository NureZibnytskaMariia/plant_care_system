from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import SensorData
from .serializers import (
    SensorDataSerializer, 
    SensorDataChartSerializer, 
    AssignSensorSerializer
)
from .services import SensorDataService


class SensorDataViewSet(mixins.CreateModelMixin,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    """ViewSet для даних сенсорів (тільки Premium)"""
    permission_classes = [IsAuthenticated]
    serializer_class = SensorDataSerializer
    
    def get_queryset(self):
        return SensorData.objects.filter(
            user_plant__user=self.request.user
        ).select_related('user_plant', 'user_plant__plant_type')
    
    def create(self, request, *args, **kwargs):
        """
        Створення запису з датчиками (використовується Arduino bridge)
        
        Цей endpoint викликається автоматично Python bridge скриптом.
        Вручну викликати не потрібно - дані надходять з Arduino.
        """
        # Перевірка Premium
        if not request.user.is_premium_active:
            return Response(
                {"detail": "Sensor features are only available for Premium users"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        method='post',
        request_body=AssignSensorSerializer,
        responses={
            200: openapi.Response(
                description='Arduino sensor assigned successfully',
                examples={
                    'application/json': {
                        'detail': 'Arduino sensor assigned successfully',
                        'plant_id': 1,
                        'plant_name': 'My Plant',
                        'instructions': {
                            'step_1': 'Copy the plant_id value',
                            'step_2': 'Open Arduino Serial Monitor',
                            'step_3': 'Send command: SET_PLANT_ID:<plant_id>',
                            'example': 'SET_PLANT_ID:1'
                        }
                    }
                }
            ),
            403: 'Premium subscription required',
            404: 'Plant not found'
        }
    )
    @action(detail=False, methods=['post'])
    def assign(self, request):
        """
        Призначити Arduino сенсор конкретній рослині
        
        Використання:
        1. Підключіть Arduino до комп'ютера
        2. Викличте цей endpoint з plant_id рослини яку хочете моніторити
        3. Відповідь містить інструкції та plant_id для налаштування Arduino
        4. Відкрийте Arduino Serial Monitor та введіть команду: SET_PLANT_ID:<plant_id>
        5. Arduino збереже ID в EEPROM та почне автоматично відправляти дані
        """
        serializer = AssignSensorSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            plant_id = serializer.validated_data['plant_id']
            
            from apps.plants.models import UserPlant
            plant = UserPlant.objects.get(id=plant_id, user=request.user)
            
            # Позначаємо що у рослини є сенсор
            plant.has_sensor = True
            plant.save(update_fields=['has_sensor'])
            
            return Response({
                "detail": "Arduino sensor assigned successfully",
                "plant_id": plant_id,
                "plant_name": plant.custom_name,
                "instructions": {
                    "step_1": "Copy the plant_id value",
                    "step_2": "Open Arduino Serial Monitor (9600 baud)",
                    "step_3": "Send command: SET_PLANT_ID:<plant_id>",
                    "step_4": "Close Serial Monitor and start Python bridge",
                    "example": f"SET_PLANT_ID:{plant_id}"
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'plant_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID рослини від якої треба відключити Arduino сенсор'
                )
            },
            required=['plant_id']
        ),
        responses={
            200: openapi.Response(
                description='Sensor unassigned successfully',
                examples={
                    'application/json': {
                        'detail': 'Arduino sensor unassigned successfully',
                        'plant_id': 1,
                        'plant_name': 'My Plant',
                        'instructions': {
                            'step_1': 'Open Arduino Serial Monitor',
                            'step_2': 'Send command: RESET',
                            'step_3': 'Arduino EEPROM cleared - ready to assign to another plant'
                        }
                    }
                }
            ),
            404: 'Plant not found'
        }
    )
    @action(detail=False, methods=['post'])
    def unassign(self, request):
        """
        Відключити Arduino сенсор від рослини
        
        Використання:
        1. Викличте цей endpoint з plant_id рослини від якої хочете відключити сенсор
        2. Відкрийте Arduino Serial Monitor
        3. Введіть команду: RESET
        4. Arduino очистить EEPROM - тепер можна призначити до іншої рослини
        """
        plant_id = request.data.get('plant_id')
        
        if not plant_id:
            return Response(
                {"detail": "plant_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.plants.models import UserPlant
            plant = UserPlant.objects.get(id=plant_id, user=request.user)
            
            # Знімаємо прапорець has_sensor
            plant.has_sensor = False
            plant.save(update_fields=['has_sensor'])
            
            return Response({
                "detail": "Arduino sensor unassigned successfully",
                "plant_id": plant_id,
                "plant_name": plant.custom_name,
                "instructions": {
                    "step_1": "Stop Python bridge (Ctrl+C)",
                    "step_2": "Open Arduino Serial Monitor (9600 baud)",
                    "step_3": "Send command: RESET",
                    "step_4": "Arduino EEPROM cleared",
                    "note": "You can now assign this Arduino to another plant using /api/sensors/assign/"
                }
            }, status=status.HTTP_200_OK)
            
        except UserPlant.DoesNotExist:
            return Response(
                {"detail": "Plant not found or does not belong to you"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @swagger_auto_schema(
        method='get',
        manual_parameters=[
            openapi.Parameter(
                'plant_id',
                openapi.IN_QUERY,
                description="ID рослини для якої показати графік",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'period',
                openapi.IN_QUERY,
                description="Період для графіку: day, week, month",
                type=openapi.TYPE_STRING,
                required=False,
                default='week'
            ),
        ],
        responses={
            200: SensorDataChartSerializer(many=True),
            400: 'plant_id is required'
        }
    )
    @action(detail=False, methods=['get'])
    def chart(self, request):
        """
        Отримати дані для графіку
        
        Повертає історичні дані з сенсорів для побудови графіків.
        """
        plant_id = request.query_params.get('plant_id')
        period = request.query_params.get('period', 'week')
        
        if not plant_id:
            return Response(
                {"detail": "plant_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.plants.models import UserPlant
        try:
            plant = UserPlant.objects.get(id=plant_id, user=request.user)
            data = SensorDataService.get_chart_data(plant, period)
            serializer = SensorDataChartSerializer(data, many=True)
            return Response(serializer.data)
        except UserPlant.DoesNotExist:
            return Response(
                {"detail": "Plant not found or does not belong to you"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @swagger_auto_schema(
        method='get',
        manual_parameters=[
            openapi.Parameter(
                'plant_id',
                openapi.IN_QUERY,
                description="ID рослини для експорту даних",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description='CSV file with sensor data',
                schema=openapi.Schema(type=openapi.TYPE_FILE)
            ),
            400: 'plant_id is required'
        }
    )
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """
        Експорт даних сенсорів у CSV формат
        
        Завантажує CSV файл з усією історією даних для рослини.
        """
        plant_id = request.query_params.get('plant_id')
        
        if not plant_id:
            return Response(
                {"detail": "plant_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.plants.models import UserPlant
        try:
            plant = UserPlant.objects.get(id=plant_id, user=request.user)
            csv_data = SensorDataService.export_to_csv(plant)
            
            response = HttpResponse(csv_data, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="sensor_data_{plant.custom_name}.csv"'
            return response
        except UserPlant.DoesNotExist:
            return Response(
                {"detail": "Plant not found or does not belong to you"},
                status=status.HTTP_404_NOT_FOUND
            )