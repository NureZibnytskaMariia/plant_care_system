from datetime import date, timedelta
from django.db.models import Max


class PlantStatusService:
    """Сервіс для розрахунку статусу рослин"""
    
    @staticmethod
    def calculate_status(plant):
        """
        Розрахунок статусу рослини
        Returns: 'healthy', 'warning', 'critical'
        """
        today = date.today()
        days_since_watering = (today - plant.last_watered_date).days
        watering_overdue = days_since_watering - plant.plant_type.watering_frequency_days
        
        if plant.user.is_premium_active and plant.has_sensor:
            return PlantStatusService._calculate_status_with_sensor(plant, watering_overdue)
        
        return PlantStatusService._calculate_status_basic(watering_overdue)
    
    @staticmethod
    def _calculate_status_with_sensor(plant, watering_overdue):
        """Розрахунок статусу з урахуванням даних сенсорів"""
        latest_sensor = plant.sensor_data.order_by('-recorded_at').first()
        
        if not latest_sensor:
            return PlantStatusService._calculate_status_basic(watering_overdue)
        
        optimal_humidity_min = plant.plant_type.optimal_humidity_min
        soil_humidity = float(latest_sensor.soil_humidity)
        
        if soil_humidity < (optimal_humidity_min * 0.5) or watering_overdue >= 3:
            return 'critical'
        
        if soil_humidity < optimal_humidity_min or watering_overdue >= 1:
            return 'warning'
        
        temp = float(latest_sensor.temperature)
        light = latest_sensor.light_level
        
        if (temp < plant.plant_type.optimal_temp_min or 
            temp > plant.plant_type.optimal_temp_max or
            light < plant.plant_type.optimal_light_min):
            return 'warning'
        
        return 'healthy'
    
    @staticmethod
    def _calculate_status_basic(watering_overdue):
        """Базовий розрахунок статусу без сенсорів"""
        if watering_overdue >= 3:
            return 'critical'
        elif watering_overdue >= 1:
            return 'warning'
        return 'healthy'


class WateringScheduleService:
    """Сервіс для управління графіком поливу"""
    
    @staticmethod
    def calculate_next_watering(plant):
        """
        Розрахунок наступної дати поливу з урахуванням сенсорів
        Returns: date
        """
        base_frequency = plant.plant_type.watering_frequency_days
        next_date = plant.last_watered_date + timedelta(days=base_frequency)
        
        if plant.user.is_premium_active and plant.has_sensor:
            adjustment = WateringScheduleService._get_sensor_adjustment(plant)
            next_date += timedelta(days=adjustment)
        
        return next_date
    
    @staticmethod
    def _get_sensor_adjustment(plant):
        """
        Розрахунок корекції графіку на основі даних сенсорів
        Returns: int (днів для додавання/віднімання)
        """
        latest_sensor = plant.sensor_data.order_by('-recorded_at').first()
        
        if not latest_sensor:
            return 0
        
        soil_humidity = float(latest_sensor.soil_humidity)
        optimal_min = plant.plant_type.optimal_humidity_min
        optimal_max = plant.plant_type.optimal_humidity_max
        
        if soil_humidity >= optimal_min:
            if soil_humidity > optimal_max:
                return 2
            return 1
        
        if soil_humidity < (optimal_min * 0.7):
            return -1 
        
        return 0
    
    @staticmethod
    def create_care_tasks(plant):
        """
        Створення завдань догляду для рослини
        Викликається після додавання рослини або завершення завдання
        """
        from apps.care.models import CareLog
        
        CareLog.objects.filter(
            user_plant=plant,
            is_completed=False,
            scheduled_date__lt=date.today()
        ).delete()
        
        if not CareLog.objects.filter(
            user_plant=plant,
            task_type='watering',
            scheduled_date=plant.next_watering_date,
            is_completed=False
        ).exists():
            CareLog.objects.create(
                user_plant=plant,
                task_type='watering',
                scheduled_date=plant.next_watering_date
            )
        
        if not CareLog.objects.filter(
            user_plant=plant,
            task_type='fertilizing',
            scheduled_date=plant.next_fertilizing_date,
            is_completed=False
        ).exists():
            CareLog.objects.create(
                user_plant=plant,
                task_type='fertilizing',
                scheduled_date=plant.next_fertilizing_date
            )
        
        if plant.next_repotting_date:
            if not CareLog.objects.filter(
                user_plant=plant,
                task_type='repotting',
                scheduled_date=plant.next_repotting_date,
                is_completed=False
            ).exists():
                CareLog.objects.create(
                    user_plant=plant,
                    task_type='repotting',
                    scheduled_date=plant.next_repotting_date
                )
    
    @staticmethod
    def complete_task(care_log):
        """
        Завершення завдання догляду та оновлення графіку рослини
        """
        from datetime import datetime
        
        care_log.is_completed = True
        care_log.completed_at = datetime.now()
        care_log.save()
        
        plant = care_log.user_plant
        
        if care_log.task_type == 'watering':
            plant.last_watered_date = care_log.scheduled_date
            plant.next_watering_date = WateringScheduleService.calculate_next_watering(plant)
        
        elif care_log.task_type == 'fertilizing':
            plant.last_fertilized_date = care_log.scheduled_date
            plant.next_fertilizing_date = plant.last_fertilized_date + timedelta(
                days=plant.plant_type.fertilizing_frequency_days
            )
        
        elif care_log.task_type == 'repotting':
            plant.last_repotted_date = care_log.scheduled_date
            if plant.plant_type.repotting_frequency_months:
                plant.next_repotting_date = plant.last_repotted_date + timedelta(
                    days=plant.plant_type.repotting_frequency_months * 30
                )
        
        plant.save()
        plant.update_status()
        
        WateringScheduleService.create_care_tasks(plant)


class CareCalendarService:
    """Сервіс для роботи з календарем догляду"""
    
    @staticmethod
    def get_tasks_for_date(user, target_date):
        """Отримати всі завдання користувача на конкретну дату"""
        from apps.care.models import CareLog
        
        return CareLog.objects.filter(
            user_plant__user=user,
            scheduled_date=target_date
        ).select_related('user_plant', 'user_plant__plant_type').order_by('task_type')
    
    @staticmethod
    def get_tasks_for_month(user, year, month):
        """Отримати всі завдання користувача за місяць"""
        from apps.care.models import CareLog
        from calendar import monthrange
        
        _, last_day = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        return CareLog.objects.filter(
            user_plant__user=user,
            scheduled_date__range=[start_date, end_date]
        ).select_related('user_plant', 'user_plant__plant_type').order_by('scheduled_date')
    
    @staticmethod
    def get_upcoming_tasks(user, days=7):
        """Отримати найближчі завдання (наступні N днів)"""
        from apps.care.models import CareLog
        
        today = date.today()
        end_date = today + timedelta(days=days)
        
        return CareLog.objects.filter(
            user_plant__user=user,
            scheduled_date__range=[today, end_date],
            is_completed=False
        ).select_related('user_plant', 'user_plant__plant_type').order_by('scheduled_date', 'task_type')
    
    @staticmethod
    def get_overdue_tasks(user):
        """Отримати прострочені завдання"""
        from apps.care.models import CareLog
        
        today = date.today()
        
        return CareLog.objects.filter(
            user_plant__user=user,
            scheduled_date__lt=today,
            is_completed=False
        ).select_related('user_plant', 'user_plant__plant_type').order_by('scheduled_date')