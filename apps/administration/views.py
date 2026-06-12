from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.users.models import User
from .serializers import (
    AdminUserSerializer,
    GrantPremiumSerializer,
    SystemStatisticsSerializer
)
from .services import AdminStatisticsService
from .permissions import IsAdminUser


class AdminUserViewSet(viewsets.ModelViewSet):
    """ViewSet для управління користувачами (тільки для адмінів)"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminUserSerializer
    queryset = User.objects.all().order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def grant_premium(self, request, pk=None):
        """Надати Premium статус"""
        user = self.get_object()
        serializer = GrantPremiumSerializer(data=request.data)
        if serializer.is_valid():
            days = serializer.validated_data['days']
            AdminStatisticsService.grant_premium(user, days)
            return Response({
                "detail": f"Premium granted for {days} days",
                "user": AdminUserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def revoke_premium(self, request, pk=None):
        """Відібрати Premium статус"""
        user = self.get_object()
        AdminStatisticsService.revoke_premium(user)
        return Response({
            "detail": "Premium revoked successfully",
            "user": AdminUserSerializer(user).data
        })
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Заблокувати/розблокувати користувача"""
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        status_text = "activated" if user.is_active else "deactivated"
        return Response({
            "detail": f"User {status_text} successfully",
            "user": AdminUserSerializer(user).data
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def system_statistics(request):
    """Отримати статистику системи"""
    stats = AdminStatisticsService.get_system_statistics()
    serializer = SystemStatisticsSerializer(stats)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def update_all_plant_statuses(request):
    """Масове оновлення статусів всіх рослин"""
    from apps.plants.models import UserPlant
    
    plants = UserPlant.objects.all()
    updated_count = 0
    
    for plant in plants:
        plant.update_status()
        updated_count += 1
    
    return Response({
        "detail": f"Updated {updated_count} plants",
        "total_plants": updated_count
    })