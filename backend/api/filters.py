from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from recipes.models import Recipe
from rest_framework import filters as filtration


User = get_user_model()


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    tags = filters.CharFilter(
        field_name='tags__slug',
        lookup_expr='in'
    )
    author = filters.ModelChoiceFilter(
        field_name='author__id',
        queryset=User.objects.all())

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'tags', 'author']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(in_cart__user=user)
        return queryset


class CustomSearchFilter(filtration.SearchFilter):
    def filter_queryset(self, request, queryset, view):
        search_param = request.query_params.get('name', '').strip()
        if search_param:
            queryset = queryset.filter(name__icontains=search_param)
        return queryset
