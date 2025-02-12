import csv
import os

from django.core.management.base import BaseCommand
from recipes.models import Tag


class Command(BaseCommand):
    help = 'Импортирует теги из CSV файла'

    def handle(self, *args, **options):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(base_dir, '..', '..', 'data', 'tags.csv')

        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(
                f'Файл {csv_file_path} не найден.'))
            return

        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                if len(row) < 2:
                    continue
                name, slug = row
                Tag.objects.get_or_create(
                    name=name.strip(), slug=slug.strip())

        self.stdout.write(self.style.SUCCESS(
            'Теги успешно импортированы из CSV'))
