from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, EmailValidator
from djoser.serializers import UserCreateSerializer as DjoserSerializer, UserSerializer
from rest_framework import serializers

import base64

from django.core.files.base import ContentFile

from recipes.constants import (MAX_LENGTH_ROLE,
                               USERNAME_SEARCH_REGEX,
                               MAX_LENGTH_EMAIL)
from recipes.models import (Ingredient,
                            Tag,
                            Recipe,
                            IngredientInRecipe,
                            RecipeTag)


import logging
logger = logging.getLogger(__name__)


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if not data:
            return None
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=f'file.{ext}')
            except (ValueError, TypeError) as e:
                raise serializers.ValidationError('Ошибка при декодировании изображения' + str(e))
        return super().to_internal_value(data)


class UserCreateSerializer(DjoserSerializer):
    username = serializers.CharField(
        max_length=MAX_LENGTH_ROLE,
        validators=[
            RegexValidator(
                regex=USERNAME_SEARCH_REGEX,
                message='Имя пользователя может содержать только буквы,'
                        ' цифры и символы: @/./+/-/_'
            )
        ]
    )
    email = serializers.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        validators=[EmailValidator(message='Некорректный email-адрес.')]
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')


class CustomUserSerializer(UserSerializer):
    avatar = Base64ImageField(required=False, use_url=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'avatar')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для промежуточной модели IngredientInRecipe.
    """
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = IngredientInRecipe
        fields = ['id', 'amount']

    def validate_amount(self, value):
        """
        Проверка количества ингредиента.
        """
        if value <= 0:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0.')
        return value


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для рецептов.
    """
    ingredients = IngredientInRecipeSerializer(many=True, required= True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(required=True)
    name = serializers.CharField(max_length=256, required=True)
    cooking_time = serializers.IntegerField(min_value=1) # Время приготовления (в минутах)

    class Meta:
        model = Recipe
        fields = [
            'name',
            'text',
            'cooking_time',
            'image',
            'author',
            'tags',
            'ingredients']

    def validate_items(self, value, item_type):
        """
        Универсальная проверка на уникальность ингредиентов и тегов.
        :param value: список объектов (ингредиентов или тегов)
        :param item_type: строка, указывающая тип (например, 'ingredient' или 'tag')
        """
        if not value:
            raise serializers.ValidationError(f'{item_type.capitalize()} должны быть указаны.')

        unique_items = set()
        item_ids = []

        for item in value:
            item_id = item.get('id') if item_type == 'ingredient' else item.id  # Для тегов используем item.id

            if not item_id:
                raise serializers.ValidationError(f'{item_type.capitalize()} должен содержать ID.')

            item_ids.append(item_id)

            # Для ингредиентов также проверяем количество
            if item_type == 'ingredient':
                amount = item.get('amount')
                if amount is None or amount <= 0:
                    raise serializers.ValidationError(
                        f'Количество {item_type} с ID {item_id} должно быть больше 0.')

            unique_items.add(item_id)

        # Если идентификаторы повторяются, выбрасываем ошибку
        if len(set(item_ids)) != len(item_ids):
            raise serializers.ValidationError(f'{item_type.capitalize()} не должны повторяться.')

        return value

    def validate_ingredients(self, value):
        """
        Проверка на уникальность ингредиентов.
        """
        return self.validate_items(value, 'ingredient')

    def validate_tags(self, value):
        """
        Проверка на уникальность тегов.
        """
        print(f"Received tags: {value}")  # Логируем входящие значения

        return value

    def validate_image(self, value):
        """
        Проверка наличия изображения.
        """
        if not value:
            raise serializers.ValidationError('Изображение должно быть предоставлено.')
        if not isinstance(value, ContentFile):
            raise serializers.ValidationError('Изображение должно быть в формате base64.')
        return value

    def create_tags_and_ingredients(self, recipe, tags, ingredients):
        """
        Создание записей в промежуточных моделях RecipeTag и IngredientInRecipe
        в одном методе.
        """
        # как по мне я тут использую избыточную трансформацию данных, как ее избежать?
        if any(isinstance(tag, Tag) for tag in tags):
            tags = [tag.id for tag in tags]
        tags = Tag.objects.filter(id__in=tags)

        tag_objects = [RecipeTag(recipe=recipe, tag=tag) for tag in tags]

        ingredient_objects = [
            IngredientInRecipe(recipe=recipe,
                               ingredient=dict(ingredient).get('id'),
                               amount=dict(ingredient).get('amount')) for ingredient in ingredients
        ]

        # Используем bulk_create для одновременного сохранения всех тегов и ингредиентов
        RecipeTag.objects.bulk_create(tag_objects)
        IngredientInRecipe.objects.bulk_create(ingredient_objects)

    def create(self, validated_data):
        """
        Переопределение метода create для сохранения рецепта с тегами и ингредиентами.
        """
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        user = self.context['request'].user

        validated_data.pop('author', None)

        recipe = Recipe.objects.create(author=user, **validated_data)

        # Сохраняем ингредиенты и теги через промежуточную модель
        self.create_tags_and_ingredients(recipe, tags, ingredients)

        return recipe

    def update(self, instance, validated_data):
        """
        Переопределение метода update для обновления рецепта с тегами и ингредиентами.
        """
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        # Обновляем основные поля рецепта
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем ингредиенты через промежуточную модель
        if ingredients_data is not None:
            instance.ingredient_amounts.all().delete()
            self.create_ingredients(instance, ingredients_data)

        # Обновляем теги через промежуточную модель
        if tags_data is not None:
            RecipeTag.objects.filter(recipe=instance).delete()
            self.create_tags(instance, tags_data)

        return instance
