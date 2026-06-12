from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date
from django.db.models import Count

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer
)


@swagger_auto_schema(
    method='post',
    request_body=UserRegistrationSerializer,
    responses={201: UserProfileSerializer}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """Реєстрація нового користувача"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    request_body=UserLoginSerializer,
    responses={200: UserProfileSerializer}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Логін користувача"""
    serializer = UserLoginSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'refresh': openapi.Schema(type=openapi.TYPE_STRING)
        },
        required=['refresh']
    )
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Logout користувача"""
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(
            {"detail": "Successfully logged out"},
            status=status.HTTP_200_OK
        )
    except Exception:
        return Response(
            {"detail": "Invalid token"},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_statistics(request):
    """Особиста статистика користувача"""
    user = request.user

    from apps.plants.models import UserPlant
    from apps.care.models import CareLog

    total_plants = UserPlant.objects.filter(user=user).count()

    plant_statuses = UserPlant.objects.filter(user=user).values('status').annotate(
        count=Count('id')
    )

    completed_tasks = CareLog.objects.filter(
        user_plant__user=user,
        is_completed=True
    ).count()

    pending_tasks = CareLog.objects.filter(
        user_plant__user=user,
        is_completed=False,
        scheduled_date__gte=date.today()
    ).count()

    overdue_tasks = CareLog.objects.filter(
        user_plant__user=user,
        is_completed=False,
        scheduled_date__lt=date.today()
    ).count()

    return Response({
        'total_plants': total_plants,
        'plant_limit': user.plant_limit,
        'is_premium': user.is_premium_active,
        'premium_days_left': (
            user.premium_end_date - date.today()
        ).days if user.is_premium_active else 0,
        'plant_statuses': {
            item['status']: item['count'] for item in plant_statuses
        },
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
    })


class UserProfileView(generics.RetrieveUpdateDestroyAPIView):
    """Профіль користувача"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def destroy(self, request, *args, **kwargs):
        """Видалення акаунту (деактивація)"""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response(
            {"detail": "Account deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )


@swagger_auto_schema(
    method='post',
    request_body=ChangePasswordSerializer
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """Зміна пароля"""
    serializer = ChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"old_password": "Wrong password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response(
            {"detail": "Password changed successfully"},
            status=status.HTTP_200_OK
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
