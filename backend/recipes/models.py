from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Модель пользователя.
    """
    email = models.EmailField(max_length=254, unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    avatar = models.ImageField(upload_to='profiles',
                               blank=True, null=True,
                               default=None)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class Tag(models.Model):
    """
    Модель тега рецепта.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """
    Модель ингредиента.
    """
    name = models.CharField(max_length=200, unique=True)
    measurement_unit = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """
    Модель рецепта.
    """
    name = models.CharField(max_length=200, blank=False, null=False)
    text = models.TextField(blank=False, null=False)
    cooking_time = models.PositiveIntegerField()  # Время приготовления (в минутах)
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)  # Картинка рецепта
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')
    tags = models.ManyToManyField(Tag, related_name='recipes')  # Теги рецепта
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes'
    )  # Ингредиенты через промежуточную таблицу
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name

class RecipeTag(models.Model):
    """
    Модель для тегов рецептов.
    """
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='tags')

    class Meta:
        unique_together = ('recipe', 'tag')  # Уникальная связь тега и рецепта
        verbose_name = "Тег рецепта"
        verbose_name_plural = "Теги рецептов"

    def __str__(self):
        return f"{self.tag.name} для {self.recipe.name}"


class IngredientInRecipe(models.Model):
    """
    Промежуточная модель для связи ингредиентов и рецептов.
    """
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredient_amounts')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='ingredient_amounts')
    amount = models.PositiveIntegerField()  # Количество ингредиента в рецепте

    class Meta:
        unique_together = ('recipe', 'ingredient')  # Уникальная связь ингредиента и рецепта
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"

    def __str__(self):
        return f"{self.ingredient.name} ({self.amount}) для {self.recipe.name}"


class FavoriteRecipe(models.Model):
    """
    Модель для избранных рецептов.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_recipes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='favorites')

    class Meta:
        unique_together = ('user', 'recipe')  # Уникальная пара user-рецепт
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"

    def __str__(self):
        return f"Избранное: {self.recipe.name} у {self.user.username}"


class ShoppingCart(models.Model):
    """
    Модель для списка покупок.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shopping_cart')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='in_cart')

    class Meta:
        unique_together = ('user', 'recipe')  # Уникальная пара user-рецепт
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"

    def __str__(self):
        return f"{self.recipe.name} в списке покупок у {self.user.username}"

class Subscription(models.Model):
    """
    Модель для подписок.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')

    class Meta:
        unique_together = ('user', 'author')  # Уникальная пара user-автор
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"{self.user.username} подписан на {self.author.username}"
