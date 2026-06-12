from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.plants.views import UserPlantViewSet
from apps.plant_types.views import PlantTypeViewSet
from apps.sensors.views import SensorDataViewSet
from apps.care.views import CareLogViewSet
from apps.administration.views import AdminUserViewSet, system_statistics, update_all_plant_statuses

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="Plant Care API",
        default_version='v1',
        description="""
# API для системи догляду за кімнатними рослинами
        """,
        contact=openapi.Contact(email="contact@plantcare.local"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


# Router для ViewSets
router = DefaultRouter()
router.register(r'plants', UserPlantViewSet, basename='plant')
router.register(r'plant-types', PlantTypeViewSet, basename='plant-type')
router.register(r'sensors', SensorDataViewSet, basename='sensor')
router.register(r'care', CareLogViewSet, basename='care')
router.register(r'admin/users', AdminUserViewSet, basename='admin-user')


urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # API Authentication
    path('api/auth/', include('apps.users.urls')),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Endpoints
    path('api/', include(router.urls)),
    
    # Admin statistics
    path('api/admin/statistics/', system_statistics, name='system-statistics'),
    path('api/admin/update-statuses/', update_all_plant_statuses, name='update-plant-statuses'),

    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]


# Media files (для фото рослин)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)