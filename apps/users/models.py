from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import date


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Email is required'))
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    LANGUAGE_CHOICES = [
        ('uk', _('Ukrainian')),
        ('en', _('English')),
    ]

    email = models.EmailField(_('email address'), unique=True, max_length=255)
    username = models.CharField(_('username'), max_length=50)
    language = models.CharField(_('language'), max_length=2, choices=LANGUAGE_CHOICES, default='uk')
    
    is_premium = models.BooleanField(_('premium status'), default=False)
    premium_start_date = models.DateField(_('premium start date'), null=True, blank=True)
    premium_end_date = models.DateField(_('premium end date'), null=True, blank=True)
    
    is_admin = models.BooleanField(_('admin status'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users'

    def __str__(self):
        return self.email

    @property
    def is_premium_active(self):
        """Перевірка чи активна преміум підписка"""
        if not self.is_premium or not self.premium_end_date:
            return False
        return self.premium_end_date >= date.today()

    @property
    def plant_limit(self):
        """Ліміт рослин для користувача"""
        return None if self.is_premium_active else 5