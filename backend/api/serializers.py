import base64
import logging

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.validators import EmailValidator, RegexValidator

from djoser.serializers import UserCreateSerializer as DjoserSerializer
from djoser.serializers import UserSerializer

from rest_framework import serializers

from recipes.constants import (
    MAX_LENGTH,
    MAX_LENGTH_EMAIL,
    MAX_LENGTH_ROLE,
    USERNAME_SEARCH_REGEX,
)
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    RecipeTag,
    ShoppingCart,
    Subscription,
    Tag,
)

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
                data = ContentFile(base64.b64decode(
                    imgstr), name=f'file.{ext}')
            except (ValueError, TypeError) as e:
                raise serializers.ValidationError(
                    'Ошибка при декодировании изображения' + str(e))
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
                  'first_name', 'last_name',
                  'password')


class CustomUserSerializer(UserSerializer):
    avatar = Base64ImageField(required=False, use_url=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'avatar',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj).exists()
        return False


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
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    name = serializers.CharField(
        source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ['id', 'name', 'measurement_unit',
                  'amount']

    def validate_amount(self, value):
        """
        Проверка количества ингредиента.
        """
        if value <= 0:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0.')
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для рецептов.
    """
    ingredients = IngredientInRecipeSerializer(many=True,
                                               required=True,
                                               allow_null=False,
                                               allow_empty=False)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
        allow_null=False,
        allow_empty=False)

    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(required=True)
    name = serializers.CharField(max_length=MAX_LENGTH,
                                 required=True)
    cooking_time = serializers.IntegerField(min_value=1)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [

            'name',
            'text',
            'cooking_time',
            'image',
            'author',
            'tags',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart']

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoriteRecipe.objects.filter(user=request.user,
                                                 recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(user=request.user,
                                           recipe=obj).exists()

    def validate(self, data):
        """
        Проверка, что поля tags и ingredients переданы и не пустые.
        """
        if 'tags' not in data or not data['tags']:
            raise serializers.ValidationError(
                {'tags': 'Теги должны быть указаны.'})

        if 'ingredients' not in data or not data['ingredients']:
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты должны быть указаны.'})

        return data

    def validate_items(self, value, item_type):
        """
        Универсальная проверка на уникальность ингредиентов и тегов.
        :param value: список объектов (ингредиентов или тегов)
        :param item_type: строка (например, 'ingredient' или 'tag')
        """

        unique_items = set()
        item_ids = []

        for item in value:
            item_id = item.get('id') if item_type == 'ingredient' else item.id

            if not item_id:
                raise serializers.ValidationError(
                    f'{item_type.capitalize()} должен содержать ID. '
                    f'Содержит:{item_id}.')

            item_ids.append(item_id)

            if item_type == 'ingredient':
                amount = item.get('amount')
                if amount is None or amount <= 0:
                    raise serializers.ValidationError(
                        f'Количество {item_type} с '
                        f'ID {item_id} должно быть больше 0.')

            unique_items.add(item_id)

        if len(set(item_ids)) != len(item_ids):
            raise serializers.ValidationError(
                f'{item_type.capitalize()} не должны повторяться.')

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

        return self.validate_items(value, 'tag')

    def validate_image(self, value):
        """
        Проверка наличия изображения.
        """
        if not value:
            raise serializers.ValidationError(
                'Изображение должно быть предоставлено.')
        if not isinstance(value, ContentFile):
            raise serializers.ValidationError(
                'Изображение должно быть в формате base64.')
        return value

    def create_tags_and_ingredients(self, recipe, tags, ingredients):
        """
        Создание записей в промежуточных моделях RecipeTag и IngredientInRecipe
        в одном методе.
        """
        if any(isinstance(tag, Tag) for tag in tags):
            tags = [tag.id for tag in tags]
        tags = Tag.objects.filter(id__in=tags)
        tag_objects = [RecipeTag(recipe=recipe, tag=tag) for tag in tags]

        ingredient_objects = [
            IngredientInRecipe(
                recipe=recipe,
                ingredient=dict(ingredient).get('id'),
                amount=dict(ingredient).get(
                    'amount')) for ingredient in ingredients
        ]

        RecipeTag.objects.bulk_create(tag_objects)
        IngredientInRecipe.objects.bulk_create(ingredient_objects)

    def create(self, validated_data):
        """
        Переопределение метода create
        для сохранения рецепта с тегами и ингредиентами.
        """
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        user = self.context['request'].user

        validated_data.pop('author', None)

        recipe = Recipe.objects.create(author=user, **validated_data)

        self.create_tags_and_ingredients(recipe, tags, ingredients)

        return recipe

    def update(self, instance, validated_data):
        """
        Переопределение метода update
        для обновления рецепта с тегами и ингредиентами.
        """
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if ingredients_data is not None or tags_data is not None:
            RecipeTag.objects.filter(recipe=instance).delete()
            instance.ingredient_amounts.all().delete()

            self.create_tags_and_ingredients(
                instance, tags_data or [], ingredients_data or [])

        return instance

    def to_representation(self, instance):
        return RecipeGetSerializer(instance).data


class RecipeGetSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeSerializer(
        many=True,
        read_only=True,
        source='ingredient_amounts')
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id',
                  'name',
                  'text',
                  'cooking_time',
                  'image',
                  'author',
                  'tags',
                  'ingredients',
                  'is_favorited',
                  'is_in_shopping_cart']

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and FavoriteRecipe.objects.filter(
                    user=request.user,
                    recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and ShoppingCart.objects.filter(
                    user=request.user,
                    recipe=obj).exists())


class RecipeShortSerializer(serializers.ModelSerializer):

    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionUserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  'recipes',
                  'recipes_count',
                  'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj).exists()
        return False

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get(
            'recipes_limit') if request else None
        recipes = Recipe.objects.filter(author=obj)
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()
