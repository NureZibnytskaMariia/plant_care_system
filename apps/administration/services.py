"""
Сервіси для адміністрування системи
"""

from django.db.models import Count, Q
from datetime import date, timedelta


class AdminStatisticsService:
    """Сервіс для адміністративної статистики"""
    
    @staticmethod
    def get_system_statistics():
        """Отримати загальну статистику системи"""
        from apps.users.models import User
        from apps.plants.models import UserPlant
        
        total_users = User.objects.filter(is_active=True).count()
        premium_users = User.objects.filter(
            is_active=True,
            is_premium=True,
            premium_end_date__gte=date.today()
        ).count()
        total_plants = UserPlant.objects.count()
        
        plant_statuses = UserPlant.objects.values('status').annotate(
            count=Count('id')
        )
        
        users_with_sensors = User.objects.filter(
            plants__has_sensor=True
        ).distinct().count()
        
        return {
            'total_users': total_users,
            'premium_users': premium_users,
            'free_users': total_users - premium_users,
            'total_plants': total_plants,
            'plant_statuses': {item['status']: item['count'] for item in plant_statuses},
            'users_with_sensors': users_with_sensors
        }
    
    @staticmethod
    def grant_premium(user, days=30):
        """Надати Premium статус користувачу"""
        user.is_premium = True
        user.premium_start_date = date.today()
        user.premium_end_date = date.today() + timedelta(days=days)
        user.save()
    
    @staticmethod
    def revoke_premium(user):
        """Відібрати Premium статус (але зберегти історію даних)"""
        user.is_premium = False
        user.save()