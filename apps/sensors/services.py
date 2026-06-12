from datetime import datetime, timedelta
import csv
from io import StringIO
import random


class SensorDataService:
    """Сервіс для роботи з даними сенсорів"""
    
    @staticmethod
    def generate_mock_data(user_plant):
        """
        Генерація тестових даних сенсорів (для емуляції без Arduino)
        """
        from apps.sensors.models import SensorData
        
        plant_type = user_plant.plant_type
        
        # Генеруємо реалістичні дані в межах оптимальних параметрів +/- 20%
        temp_range = (plant_type.optimal_temp_min, plant_type.optimal_temp_max)
        humidity_range = (plant_type.optimal_humidity_min, plant_type.optimal_humidity_max)
        light_range = (plant_type.optimal_light_min, plant_type.optimal_light_max)
        
        temp = random.uniform(
            float(temp_range[0]) * 0.9,
            float(temp_range[1]) * 1.1
        )
        
        # ЗМІНЕНО: Генеруємо air_humidity (вологість повітря)
        air_humidity = random.uniform(
            humidity_range[0] * 0.8,
            humidity_range[1] * 1.2
        )
        
        # ДОДАНО: Опціонально генеруємо soil_humidity
        # Якщо є датчик - можна генерувати, якщо ні - None
        soil_humidity = None  # Або random.uniform(30, 70) якщо датчик є
        
        light = random.randint(
            int(light_range[0] * 0.8),
            int(light_range[1] * 1.2)
        )
        
        sensor_data = SensorData.objects.create(
            user_plant=user_plant,
            temperature=round(temp, 1),
            soil_humidity=round(soil_humidity, 2) if soil_humidity else None,
            air_humidity=round(air_humidity, 2),
            light_level=light
        )
        
        user_plant.update_status()
        
        return sensor_data
    
    @staticmethod
    def get_chart_data(user_plant, period='week'):
        """
        Отримати дані для графіку
        period: 'day', 'week', 'month'
        """
        from apps.sensors.models import SensorData
        
        now = datetime.now()
        
        if period == 'day':
            start_time = now - timedelta(days=1)
        elif period == 'week':
            start_time = now - timedelta(days=7)
        elif period == 'month':
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=7)
        
        data = SensorData.objects.filter(
            user_plant=user_plant,
            recorded_at__gte=start_time
        ).order_by('recorded_at').values(
            'temperature',
            'soil_humidity',
            'air_humidity',  # ДОДАНО
            'light_level',
            'recorded_at'
        )
        
        return list(data)
    
    @staticmethod
    def export_to_csv(user_plant):
        """
        Експорт даних сенсорів у CSV формат
        """
        from apps.sensors.models import SensorData
        
        output = StringIO()
        writer = csv.writer(output)
        
        # ОНОВЛЕНО: додано air_humidity
        writer.writerow([
            'Date/Time',
            'Temperature (°C)',
            'Air Humidity (%)',
            'Soil Humidity (%)',
            'Light Level (lux)'
        ])
        
        sensor_data = SensorData.objects.filter(
            user_plant=user_plant
        ).order_by('-recorded_at')
        
        for data in sensor_data:
            writer.writerow([
                data.recorded_at.strftime('%Y-%m-%d %H:%M:%S'),
                data.temperature,
                data.air_humidity if data.air_humidity else 'N/A',
                data.soil_humidity if data.soil_humidity else 'N/A',
                data.light_level
            ])
        
        return output.getvalue()