from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db import models
from .models import PlantType
from .serializers import PlantTypeSerializer, PlantTypeCreateSerializer


class PlantTypeViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin, 
                      mixins.DestroyModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """
    ViewSet для каталогу типів рослин
    
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PlantType.objects.filter(
            models.Q(is_custom=False) |
            models.Q(created_by_user=self.request.user)
        )
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PlantTypeCreateSerializer
        return PlantTypeSerializer
    
    def perform_create(self, serializer):
        serializer.save(
            created_by_user=self.request.user,
            is_custom=True
        )
    
    def perform_update(self, serializer):
        plant_type = self.get_object()
        if not plant_type.is_custom or plant_type.created_by_user != self.request.user:
            raise PermissionDenied("You can only edit your own custom plant types")
        serializer.save()
    
    def perform_destroy(self, instance):
        if not instance.is_custom or instance.created_by_user != self.request.user:
            raise PermissionDenied("You can only delete your own custom plant types")
        instance.delete()