from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from datetime import date, timedelta

class UserPlant(models.Model):
    STATUS_CHOICES = [
        ('healthy', _('Healthy')),
        ('warning', _('Needs Attention')),
        ('critical', _('Critical')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='plants',
        verbose_name=_('user')
    )
    plant_type = models.ForeignKey(
        'plant_types.PlantType',
        on_delete=models.PROTECT,
        related_name='user_plants',
        verbose_name=_('plant type')
    )
    
    custom_name = models.CharField(_('custom name'), max_length=100)
    location = models.CharField(_('location'), max_length=100, blank=True, null=True)
    photo = models.ImageField(
        _('photo'), 
        upload_to='plant_photos/', 
        blank=True, 
        null=True
    )
    
    last_watered_date = models.DateField(_('last watered'))
    last_fertilized_date = models.DateField(_('last fertilized'))
    last_repotted_date = models.DateField(_('last repotted'), blank=True, null=True)
    
    next_watering_date = models.DateField(_('next watering'))
    next_fertilizing_date = models.DateField(_('next fertilizing'))
    next_repotting_date = models.DateField(_('next repotting'), blank=True, null=True)
    
    status = models.CharField(
        _('status'), 
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='healthy'
    )
    has_sensor = models.BooleanField(_('has sensor'), default=False)
    notes = models.TextField(_('notes'), blank=True, null=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('user plant')
        verbose_name_plural = _('user plants')
        db_table = 'user_plants'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.custom_name} ({self.user.username})"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.calculate_next_dates()
        super().save(*args, **kwargs)

    def calculate_next_dates(self):
        self.next_watering_date = self.last_watered_date + timedelta(
            days=self.plant_type.watering_frequency_days
        )
        self.next_fertilizing_date = self.last_fertilized_date + timedelta(
            days=self.plant_type.fertilizing_frequency_days
        )
        if self.last_repotted_date and self.plant_type.repotting_frequency_months:
            self.next_repotting_date = self.last_repotted_date + timedelta(
                days=self.plant_type.repotting_frequency_months * 30
            )

    def update_status(self):
        from apps.plants.services import PlantStatusService
        self.status = PlantStatusService.calculate_status(self)
        self.save(update_fields=['status'])