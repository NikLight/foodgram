import csv
import os
from django.core.files import File
from django.core.management.base import BaseCommand
from recipes.models import Recipe, Tag, Ingredient, IngredientInRecipe, User

class Command(BaseCommand):
    help = 'Импортирует рецепты из CSV файла'

    def handle(self, *args, **options):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, '..', '..', 'data')
        csv_file_path = os.path.join(data_dir, 'recipes.csv')

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
                    image_filename = row['image'].strip()
                    author_id = int(row['author_id'])

                    author = User.objects.get(id=author_id)

                    if Recipe.objects.filter(name=name).exists():
                        self.stdout.write(self.style.WARNING(f'Рецепт "{name}" уже существует. Пропускаем.'))
                        continue

                    recipe = Recipe.objects.create(
                        name=name,
                        text=text,
                        cooking_time=cooking_time,
                        author=author,
                    )

                    image_path = os.path.join(data_dir, image_filename)
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as img_file:
                            recipe.image.save(image_filename, File(img_file), save=True)
                    else:
                        self.stdout.write(self.style.WARNING(f'Изображение "{image_filename}" не найдено. Пропускаем.'))

                    tags_ids = row['tags'].split(';')
                    for tag_id in tags_ids:
                        tag = Tag.objects.get(id=int(tag_id))
                        recipe.tags.add(tag)

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
