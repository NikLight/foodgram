from django.contrib.auth import get_user_model
from django.db.models import Q
from django_filters import rest_framework as filters
from recipes.models import Recipe

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug'
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


class IngredientSearchFilter(filters.SearchFilter):
    def filter_queryset(self, request, queryset, view):
        search_param = request.query_params.get('search', '').strip()
        if not search_param:
            return queryset

        starts_with = queryset.filter(name__istartswith=search_param)

        contains = queryset.filter(
            Q(name__icontains=search_param) & ~Q(
                id__in=starts_with.values('id'))
        )

        return starts_with.union(contains).order_by('name')
