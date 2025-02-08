import csv
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Импортирует суперпользователей из CSV файла'

    def handle(self, *args, **options):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(
            base_dir, '..', '..', 'data', 'superusers.csv')

        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(
                f'Файл {csv_file_path} не найден.'))
            return

        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    email = row['email'].strip()
                    username = row['username'].strip()
                    password = row['password'].strip()
                    first_name = row.get('first_name', '').strip()
                    last_name = row.get('last_name', '').strip()
                    avatar = row.get('avatar', '').strip()

                    if User.objects.filter(email=email).exists():
                        self.stdout.write(self.style.WARNING(
                            f'Пользователь с email "{email}" уже существует.'
                            f' Пропускаем.'))
                        continue

                    user = User.objects.create_superuser(
                        email=email,
                        username=username,
                        password=password
                    )
                    user.first_name = first_name
                    user.last_name = last_name

                    if avatar:
                        user.avatar = avatar

                    user.save()
                    self.stdout.write(self.style.SUCCESS(
                        f'Суперпользователь "{username}" успешно создан.'))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'Ошибка при создании суперпользователя: {e}'))

        self.stdout.write(self.style.SUCCESS(
            'Импорт суперпользователей завершен.'))
