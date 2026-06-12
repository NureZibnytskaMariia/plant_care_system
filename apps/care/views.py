from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import date, datetime, timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import CareLog
from .serializers import CareLogSerializer, CompleteCareTaskSerializer
from apps.plants.services import WateringScheduleService


class CareLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для завдань догляду"""
    permission_classes = [IsAuthenticated]
    serializer_class = CareLogSerializer
    
    def get_queryset(self):
        return CareLog.objects.filter(
            user_plant__user=self.request.user
        ).select_related('user_plant', 'user_plant__plant_type')
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Завдання на сьогодні"""
        tasks = self.get_queryset().filter(
            scheduled_date=date.today(),
            is_completed=False
        )
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Найближчі завдання (7 днів)"""
        end_date = date.today() + timedelta(days=7)
        tasks = self.get_queryset().filter(
            scheduled_date__range=[date.today(), end_date],
            is_completed=False
        ).order_by('scheduled_date')
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Прострочені завдання"""
        tasks = self.get_queryset().filter(
            scheduled_date__lt=date.today(),
            is_completed=False
        ).order_by('scheduled_date')
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        operation_description='Отримати завдання за конкретний місяць',
        manual_parameters=[
            openapi.Parameter(
                'year',
                openapi.IN_QUERY,
                description="Рік (наприклад: 2024)",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'month',
                openapi.IN_QUERY,
                description="Місяць (1-12)",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
        ],
        responses={
            200: CareLogSerializer(many=True),
            400: 'Bad Request - year and month parameters are required'
        }
    )
    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Завдання за місяць"""
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        
        if not year or not month:
            return Response(
                {"detail": "year and month parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            year = int(year)
            month = int(month)
        except ValueError:
            return Response(
                {"detail": "year and month must be integers"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if month < 1 or month > 12:
            return Response(
                {"detail": "month must be between 1 and 12"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.plants.services import CareCalendarService
        tasks = CareCalendarService.get_tasks_for_month(request.user, year, month)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        operation_description='Отримати завдання на конкретну дату',
        manual_parameters=[
            openapi.Parameter(
                'date',
                openapi.IN_QUERY,
                description="Дата у форматі YYYY-MM-DD (наприклад: 2024-12-17)",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        responses={
            200: CareLogSerializer(many=True),
            400: 'Bad Request - date parameter is required or invalid format'
        }
    )
    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """Завдання на конкретну дату"""
        target_date = request.query_params.get('date')
        
        if not target_date:
            return Response(
                {"detail": "date parameter is required (format: YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.plants.services import CareCalendarService
        tasks = CareCalendarService.get_tasks_for_date(request.user, parsed_date)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Відмітити завдання як виконане"""
        task = self.get_object()
        
        if task.is_completed:
            return Response(
                {"detail": "Task is already completed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CompleteCareTaskSerializer(data=request.data)
        if serializer.is_valid():
            WateringScheduleService.complete_task(task)
            if serializer.validated_data.get('notes'):
                task.notes = serializer.validated_data['notes']
                task.save()
            return Response({"detail": "Task completed successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def skip(self, request, pk=None):
        """Пропустити завдання"""
        task = self.get_object()
        
        if task.is_completed:
            return Response(
                {"detail": "Cannot skip completed task"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if task.skipped:
            return Response(
                {"detail": "Task is already skipped"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.skipped = True
        task.save()
        
        return Response({"detail": "Task skipped successfully"})