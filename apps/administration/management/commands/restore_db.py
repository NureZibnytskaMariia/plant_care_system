"""
Django management command для відновлення БД з резервної копії
Використання: python manage.py restore_db backup_20241211_120000.sqlite3
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from datetime import datetime
import shutil
import os


class Command(BaseCommand):
    help = 'Відновити базу даних з резервної копії'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Назва файлу backup для відновлення',
        )

    def handle(self, *args, **options):
        backup_name = options['backup_file']
        backup_dir = settings.BASE_DIR / 'backups'
        
        if not backup_name.endswith('.sqlite3'):
            backup_name += '.sqlite3'
        
        backup_path = backup_dir / backup_name
        
        if not backup_path.exists():
            raise CommandError(f'Backup файл не знайдено: {backup_path}')
        
        db_path = settings.DATABASES['default']['NAME']
        
        confirm = input(
            f'\n УВАГА! Це видалить поточну БД і замінить її на backup.\n'
            f'   Поточна БД: {db_path}\n'
            f'   Backup: {backup_path}\n\n'
            f'   Продовжити? (yes/no): '
        )
        
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.WARNING('Відновлення скасовано'))
            return
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            current_backup = backup_dir / f'before_restore_{timestamp}.sqlite3'
            shutil.copy2(db_path, current_backup)
            self.stdout.write(f'Поточну БД збережено як: {current_backup}')
            
            shutil.copy2(backup_path, db_path)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ БД успішно відновлено з {backup_name}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Помилка при відновленні: {str(e)}')
            )