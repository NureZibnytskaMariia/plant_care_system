from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class PlantType(models.Model):
    name_uk = models.CharField(_('name (Ukrainian)'), max_length=100)
    name_en = models.CharField(_('name (English)'), max_length=100)
    scientific_name = models.CharField(_('scientific name'), max_length=150, blank=True, null=True)
    
    watering_frequency_days = models.PositiveIntegerField(_('watering frequency (days)'))
    fertilizing_frequency_days = models.PositiveIntegerField(_('fertilizing frequency (days)'))
    repotting_frequency_months = models.PositiveIntegerField(
        _('repotting frequency (months)'), 
        blank=True, 
        null=True
    )
    
    optimal_temp_min = models.DecimalField(
        _('optimal temperature min (°C)'), 
        max_digits=4, 
        decimal_places=1
    )
    optimal_temp_max = models.DecimalField(
        _('optimal temperature max (°C)'), 
        max_digits=4, 
        decimal_places=1
    )
    optimal_humidity_min = models.PositiveIntegerField(_('optimal humidity min (%)'))
    optimal_humidity_max = models.PositiveIntegerField(_('optimal humidity max (%)'))
    optimal_light_min = models.PositiveIntegerField(_('optimal light min (lux)'))
    optimal_light_max = models.PositiveIntegerField(_('optimal light max (lux)'))
    
    description_uk = models.TextField(_('description (Ukrainian)'))
    description_en = models.TextField(_('description (English)'))
    care_tips_uk = models.TextField(_('care tips (Ukrainian)'), blank=True, null=True)
    care_tips_en = models.TextField(_('care tips (English)'), blank=True, null=True)
    
    is_custom = models.BooleanField(_('custom plant'), default=False)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='custom_plant_types',
        verbose_name=_('created by')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('plant type')
        verbose_name_plural = _('plant types')
        db_table = 'plant_types'
        ordering = ['name_en']

    def __str__(self):
        return f"{self.name_en} / {self.name_uk}"