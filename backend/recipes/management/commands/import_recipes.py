import csv
import os
import base64
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from recipes.models import Recipe, Tag, Ingredient, IngredientInRecipe, User


class Command(BaseCommand):
    help = 'Импортирует рецепты из CSV файла'

    def handle(self, *args, **options):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(base_dir, '..', '..', 'data', 'recipes.csv')

        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'Файл {csv_file_path} не найден.'))
            return

        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    name = row['name'].strip()
                    text = row['text'].strip()
                    cooking_time = int(row['cooking_time'])
                    image_data = row['image'].strip()
                    author_id = int(row['author_id'])

                    author = User.objects.get(id=author_id)

                    if Recipe.objects.filter(name=name).exists():
                        self.stdout.write(self.style.WARNING(f'Рецепт "{name}" уже существует. Пропускаем.'))
                        continue

                    # Обрабатываем изображение
                    image = None
                    if image_data.startswith('data:image'):
                        format, imgstr = image_data.split(';base64,')
                        ext = format.split('/')[-1]
                        image = ContentFile(base64.b64decode(imgstr), name=f'{name.replace(" ", "_")}.{ext}')

                    # Создаем рецепт
                    recipe, created = Recipe.objects.get_or_create(
                        name=name,
                        text=text,
                        cooking_time=cooking_time,
                        author=author,
                    )

                    # Если изображение есть, добавляем его
                    if image:
                        recipe.image.save(image.name, image, save=True)

                    # Добавляем теги
                    tags_ids = row['tags'].split(';')
                    for tag_id in tags_ids:
                        tag = Tag.objects.get(id=int(tag_id))
                        recipe.tags.add(tag)

                    # Добавляем ингредиенты
                    ingredients_data = row['ingredients'].split(';')
                    for ingredient_data in ingredients_data:
                        ingredient_id, amount = ingredient_data.split(':')
                        ingredient = Ingredient.objects.get(id=int(ingredient_id))
                        IngredientInRecipe.objects.create(
                            recipe=recipe,
                            ingredient=ingredient,
                            amount=int(amount)
                        )

                    recipe.save()
                    self.stdout.write(self.style.SUCCESS(f'Рецепт "{name}" успешно добавлен.'))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Ошибка при добавлении рецепта: {e}'))

        self.stdout.write(self.style.SUCCESS('Импорт рецептов завершен.'))
