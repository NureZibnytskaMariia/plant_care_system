from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import UserPlant
from .serializers import UserPlantSerializer, UserPlantCreateSerializer


class UserPlantViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin, 
                      mixins.DestroyModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """
    ViewSet для управління рослинами користувача
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserPlant.objects.filter(
            user=self.request.user
        ).select_related('plant_type')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserPlantCreateSerializer
        return UserPlantSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Видалити рослину з усіма пов'язаними даними"""
        plant = self.get_object()
        plant_name = plant.custom_name
        plant.delete()
        return Response(
            {"detail": f"Plant '{plant_name}' deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )