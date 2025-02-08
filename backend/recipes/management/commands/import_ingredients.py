import csv
import os

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импортирует ингредиенты из CSV и JSON файлов'

    def handle(self, *args, **options):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(
            base_dir, '..', '..', 'data', 'ingredients.csv')

        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            for row in reader:
                name, measurement_unit = row
                Ingredient.objects.get_or_create(
                    name=name.strip(),
                    measurement_unit=measurement_unit.strip())
        self.stdout.write(self.style.SUCCESS(
            'Ингредиенты успешно импортированы из CSV'))
