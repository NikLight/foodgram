from django_filters import rest_framework as filters
from recipes.models import Recipe, Tag


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_is_in_shopping_cart')

    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),  # Все теги из базы
        field_name='tags__slug',  # Указываем, что фильтр должен использовать поле slug
        to_field_name='slug',  # Фильтруем по slug
        conjoined=False  # Для поддержки фильтрации по нескольким тегам
    )
    author = filters.NumberFilter(field_name='author__id')

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'tags', 'author']

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(is_favorited=True)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(is_in_shopping_cart=True)
        return queryset

