from django.db import models
from django.utils.translation import gettext_lazy as _


class SensorData(models.Model):
    user_plant = models.ForeignKey(
        'plants.UserPlant',
        on_delete=models.CASCADE,
        related_name='sensor_data',
        verbose_name=_('plant')
    )
    
    temperature = models.DecimalField(
        _('temperature (°C)'),
        max_digits=4,
        decimal_places=1
    )
    
    # ЗМІНЕНО: soil_humidity тепер опціональний
    soil_humidity = models.DecimalField(
        _('soil humidity (%)'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Optional - only if soil moisture sensor is available')
    )
    
    # ДОДАНО: вологість повітря з DHT11
    air_humidity = models.DecimalField(
        _('air humidity (%)'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Air humidity from DHT11 sensor')
    )
    
    light_level = models.PositiveIntegerField(_('light level (lux)'))
    
    recorded_at = models.DateTimeField(_('recorded at'), auto_now_add=True)

    class Meta:
        verbose_name = _('sensor data')
        verbose_name_plural = _('sensor data')
        db_table = 'sensor_data'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['user_plant', '-recorded_at']),
        ]

    def __str__(self):
        return f"{self.user_plant.custom_name} - {self.recorded_at}"