from django.db import models
from django.utils.translation import gettext_lazy as _

class CareLog(models.Model):
    TASK_TYPE_CHOICES = [
        ('watering', _('Watering')),
        ('fertilizing', _('Fertilizing')),
        ('repotting', _('Repotting')),
    ]

    user_plant = models.ForeignKey(
        'plants.UserPlant',
        on_delete=models.CASCADE,
        related_name='care_logs',
        verbose_name=_('plant')
    )
    
    scheduled_date = models.DateField(_('scheduled date'))
    task_type = models.CharField(
        _('task type'), 
        max_length=12, 
        choices=TASK_TYPE_CHOICES
    )
    
    is_completed = models.BooleanField(_('completed'), default=False)
    completed_at = models.DateTimeField(_('completed at'), blank=True, null=True)
    skipped = models.BooleanField(_('skipped'), default=False)
    auto_adjusted = models.BooleanField(
        _('auto adjusted by sensor'), 
        default=False
    )
    
    notes = models.TextField(_('notes'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('care log')
        verbose_name_plural = _('care logs')
        db_table = 'care_logs'
        ordering = ['scheduled_date', '-created_at']
        indexes = [
            models.Index(fields=['user_plant', 'scheduled_date']),
            models.Index(fields=['scheduled_date', 'is_completed']),
        ]

    def __str__(self):
        return f"{self.user_plant.custom_name} - {self.get_task_type_display()} on {self.scheduled_date}"