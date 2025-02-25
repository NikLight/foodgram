from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from .constants import (MAX_LENGTH, MAX_LENGTH_INGREDIENT,
                        MAX_LENGTH_MEASURMENT_UNIT, MAX_LENGTH_RECIPE,
                        MAX_LENGTH_ROLE, MAX_LENGTH_TAG)


class User(AbstractUser):
    """
    Модель пользователя.
    """
    email = models.EmailField(max_length=MAX_LENGTH, unique=True)
    username = models.CharField(max_length=MAX_LENGTH_ROLE, unique=True)
    first_name = models.CharField(max_length=MAX_LENGTH_ROLE)
    last_name = models.CharField(max_length=MAX_LENGTH_ROLE)
    avatar = models.ImageField(upload_to='profiles',
                               blank=True, null=True,
                               default=None)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class Tag(models.Model):
    """
    Модель тега рецепта.
    """
    name = models.CharField(max_length=MAX_LENGTH_TAG, unique=True)
    slug = models.SlugField(max_length=MAX_LENGTH_TAG, unique=True)

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """
    Модель ингредиента.
    """
    name = models.CharField(max_length=MAX_LENGTH_INGREDIENT, unique=True)
    measurement_unit = models.CharField(max_length=MAX_LENGTH_MEASURMENT_UNIT)

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """
    Модель рецепта.
    """
    name = models.CharField(
        max_length=MAX_LENGTH_RECIPE, blank=False, null=False)
    text = models.TextField(
        blank=False, null=False)
    cooking_time = models.PositiveIntegerField()
    image = models.ImageField(
        upload_to='recipes/', blank=True, null=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes')
    tags = models.ManyToManyField(
        Tag, through='RecipeTag', related_name='recipes')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes'
    )
    pub_date = models.DateTimeField('Дата публикации',
                                    auto_now_add=True)

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        #ordering = ['-pub_date']

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    """
    Модель для тегов рецептов.
    """
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,)
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE,)

    class Meta:
        ordering = ('recipe', 'tag')
        unique_together = ('recipe', 'tag')
        verbose_name = "Тег рецепта"
        verbose_name_plural = "Теги рецептов"

    def __str__(self):
        return f"{self.tag.name} для {self.recipe.name}"


class IngredientInRecipe(models.Model):
    """
    Промежуточная модель для связи ингредиентов и рецептов.
    """
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='ingredient_amounts')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='ingredient_amounts')
    amount = models.PositiveIntegerField()

    class Meta:
        unique_together = ('recipe', 'ingredient')
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"

    def __str__(self):
        return f"{self.ingredient.name} ({self.amount}) для {self.recipe.name}"


class FavoriteRecipe(models.Model):
    """
    Модель для избранных рецептов.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='favorite_recipes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='favorites')

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"

    def __str__(self):
        return f"Избранное: {self.recipe.name} у {self.user.username}"


class ShoppingCart(models.Model):
    """
    Модель для списка покупок.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='shopping_cart')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='in_cart')

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"

    def __str__(self):
        return (f"{self.recipe.name} в списке покупок"
                f" у {self.user.username}")


class Subscription(models.Model):
    """
    Модель для подписок.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='following')

    class Meta:
        unique_together = ('user', 'author')
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя')

    def __str__(self):
        return f"{self.user.username} подписан на {self.author.username}"
