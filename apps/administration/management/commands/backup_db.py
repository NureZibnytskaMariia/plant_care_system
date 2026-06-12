"""
Django management command для створення резервної копії БД
Використання: python manage.py backup_db [--name custom_name]
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from datetime import datetime
import shutil
import os


class Command(BaseCommand):
    help = 'Створити резервну копію бази даних SQLite'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            help='Назва файлу backup (за замовчуванням - дата та час)',
        )

    def handle(self, *args, **options):
        db_path = settings.DATABASES['default']['NAME']
        
        backup_dir = settings.BASE_DIR / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        if options['name']:
            backup_name = f"{options['name']}.sqlite3"
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}.sqlite3"
        
        backup_path = backup_dir / backup_name
        
        try:
            shutil.copy2(db_path, backup_path)
            
            size_mb = os.path.getsize(backup_path) / (1024 * 1024)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f' Резервну копію створено успішно!\n'
                    f'  Файл: {backup_path}\n'
                    f'  Розмір: {size_mb:.2f} MB'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Помилка при створенні backup: {str(e)}')
            )