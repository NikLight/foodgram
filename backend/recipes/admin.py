from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (FavoriteRecipe, Ingredient, IngredientInRecipe, Recipe,
                     RecipeTag, ShoppingCart, Subscription, Tag, User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Админка для модели пользователя.
    """
    model = User
    list_display = ('id', 'email', 'username',
                    'first_name', 'last_name', 'is_staff',
                    'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'username',
                     'first_name', 'last_name')
    ordering = ('id',)
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name',
                                                'avatar')}),
        ('Права доступа', {'fields': ('is_staff', 'is_active',
                                      'is_superuser', 'groups',
                                      'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1',
                       'password2', 'is_staff', 'is_active'),
        }),
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Админка для модели тегов.
    """
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('id',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """
    Админка для модели ингредиентов.
    """
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    ordering = ('id',)


class IngredientInRecipeInline(admin.TabularInline):
    """
    Inline для отображения ингредиентов в рецепте.
    """
    model = IngredientInRecipe
    extra = 1


class RecipeTagInline(admin.TabularInline):
    """
    Inline для отображения тегов в рецепте.
    """
    model = RecipeTag
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Админка для модели рецептов.
    """
    list_display = ('id', 'name', 'author', 'cooking_time', 'pub_date')
    list_filter = ('author', 'tags', 'pub_date')
    search_fields = ('name', 'author__username', 'author__email')
    inlines = [IngredientInRecipeInline, RecipeTagInline]
    ordering = ('-pub_date',)

    def favorites_count(self, obj):
        """Отображает количество добавлений рецепта в избранное."""
        return obj.favorites.count()
    favorites_count.short_description = 'В избранном'


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    """
    Админка для избранных рецептов.
    """
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    ordering = ('id',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """
    Админка для списка покупок.
    """
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    ordering = ('id',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """
    Админка для подписок.
    """
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')
    ordering = ('id',)
