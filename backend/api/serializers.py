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
                            Recipe)


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'file.{ext}')
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
        fields = ['id', 'name', 'slug']

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']

class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    #ingredients = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(), many=True)
    #tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    #ingredients_names = serializers.SerializerMethodField()
    #tags_names = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'image', 'name', 'text', 'cooking_time', 'author', 'tags', 'ingredients']

#     def create(self, validated_data):
#         ingredients_data = validated_data.pop('ingredients')
#         recipe = Recipe.objects.create(**validated_data)
#         for ingredient_data in ingredients_data:
#             IngredientInRecipe.objects.create(recipe=recipe, **ingredient_data)
#         return recipe
#
#     def update(self, instance, validated_data):
#         ingredients_data = validated_data.pop('ingredients', None)
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()
#
#         if ingredients_data is not None:
#             # Удаляем старые ингредиенты и добавляем новые
#             instance.ingredients.all().delete()
#             for ingredient_data in ingredients_data:
#                 IngredientInRecipe.objects.create(recipe=instance, **ingredient_data)
#
#         return instance
#
#     def get_ingredients_names(self, obj):
#         return [ingredient.name for ingredient in obj.ingredients.all()]
#
#     def get_tags_names(self, obj):
#         return [tag.name for tag in obj.tags.all()]
