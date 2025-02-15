import os
from io import BytesIO

import requests
import short_url

from django.contrib.auth import get_user_model
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserViewSet
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from recipes.constants import FreeSans_Link
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
)

from .filters import CustomSearchFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrAdmin
from .serializers import (
    Base64ImageField,
    CustomUserSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeGetSerializer,
    RecipeShortSerializer,
    SubscriptionUserSerializer,
    TagSerializer,
)

User = get_user_model()


def generate_short_link(request, recipe_id):
    short_code = short_url.encode_url(recipe_id)

    base_url = request.build_absolute_uri('/')[:-1]
    return f"{base_url}/s/{short_code}"


def redirect_to_recipe(request, s):
    try:
        pk = short_url.decode_url(s)
        recipe = get_object_or_404(Recipe, pk=pk)
        return redirect(f'/recipes/{recipe.pk}/')
    except ValueError:
        raise Http404("Неверный короткий URL")


class UserViewSet(DjoserViewSet):
    queryset = User.objects.all().order_by('id')
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            avatar = request.data.get('avatar')
            if avatar:
                try:
                    user.avatar = Base64ImageField().to_internal_value(avatar)
                    user.save()
                    serializer = CustomUserSerializer(user)
                    return Response(serializer.data,
                                    status=status.HTTP_200_OK)
                except ValidationError as e:
                    return Response({"detail": str(e)},
                                    status=status.HTTP_400_BAD_REQUEST)
            return Response(
                {"detail": "Файл 'avatar' не найден."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.avatar.delete(save=True)
        user.save()
        serializer = CustomUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='subscriptions',
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(
            user=user).select_related('author')
        page = self.paginate_queryset(subscriptions)

        if page is not None:
            authors_for_page = []
            for subscription in page:
                authors_for_page.append(subscription.author)

            serializer = SubscriptionUserSerializer(
                authors_for_page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        authors_for_subscriptions = []
        for subscription in subscriptions:
            authors_for_subscriptions.append(subscription.author)
        serializer = SubscriptionUserSerializer(
            authors_for_subscriptions,
            many=True,
            context={'request': request})
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe',
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        """Позволяет подписываться и отписываться от пользователей."""
        user = request.user
        author = get_object_or_404(User, pk=id)

        if request.method == 'POST':

            Subscription.objects.create(user=user, author=author)

            recipes_limit = request.query_params.get('recipes_limit', None)
            recipes = Recipe.objects.filter(author=author)
            if recipes_limit:
                try:
                    recipes_limit = int(recipes_limit)
                    recipes = recipes[:recipes_limit]
                except ValueError:
                    return Response(
                        {"detail": "Неверное значение параметра"
                                   " 'recipes_limit'."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            serializer = SubscriptionUserSerializer(
                author, context={'request': request})
            response_data = serializer.data
            response_data['recipes'] = RecipeShortSerializer(
                recipes, many=True).data

            return Response(response_data,
                            status=status.HTTP_201_CREATED)

        subscription = Subscription.objects.filter(user=user,
                                                   author=author).first()
        if not subscription:
            return Response(
                {"detail": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(
            {"detail": "Вы успешно отписались."},
            status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [CustomSearchFilter]
    search_fields = ['^name']
    pagination_class = None


class UserRecipeRelationMixin:
    relation_model = None
    success_add_message = "Рецепт успешно добавлен."
    success_remove_message = "Рецепт успешно удалён."
    already_exists_message = "Рецепт уже существует."
    not_exists_message = "Рецепт не найден."

    def add_relation(self, user, recipe):
        if self.relation_model.objects.filter(user=user,
                                              recipe=recipe).exists():
            return Response(
                {"detail": self.already_exists_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.relation_model.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(recipe,
                                           context={'request': self.request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_relation(self, user, recipe):
        relation_instance = self.relation_model.objects.filter(
            user=user, recipe=recipe).first()
        if not relation_instance:
            return Response(
                {"detail": self.not_exists_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        relation_instance.delete()
        return Response(
            {"detail": self.success_remove_message},
            status=status.HTTP_204_NO_CONTENT
        )


class RecipeViewSet(viewsets.ModelViewSet, UserRecipeRelationMixin):
    queryset = Recipe.objects.all().order_by('-pub_date')
    permission_classes = [AllowAny]
    pagination_class = CustomPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeGetSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthorOrAdmin]
        return super().get_permissions()

    @action(detail=True, methods=['post', 'delete'], url_path='favorite',
            permission_classes=[IsAuthenticated])
    def manage_favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        self.relation_model = FavoriteRecipe
        self.success_add_message = "Рецепт успешно добавлен в избранное."
        self.success_remove_message = "Рецепт успешно удалён из избранного."
        self.already_exists_message = "Рецепт уже в избранном."
        self.not_exists_message = "Рецепт не в избранном."

        if request.method == 'POST':
            return self.add_relation(user, recipe)
        elif request.method == 'DELETE':
            return self.remove_relation(user, recipe)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart',
            permission_classes=[IsAuthenticated])
    def manage_shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        self.relation_model = ShoppingCart
        self.success_add_message = ("Рецепт успешно добавлен в"
                                    " список покупок.")
        self.success_remove_message = ("Рецепт успешно удалён из"
                                       " списка покупок.")
        self.already_exists_message = ("Рецепт уже в"
                                       " списке покупок.")
        self.not_exists_message = ("Рецепт не в"
                                   " списке покупок.")

        if request.method == 'POST':
            return self.add_relation(user, recipe)
        elif request.method == 'DELETE':
            return self.remove_relation(user, recipe)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart',
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user)
        recipes = Recipe.objects.filter(
            in_cart__in=shopping_cart).prefetch_related(
            'ingredients')

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)

        font_url = FreeSans_Link
        local_font_path = os.path.join(
            'static',
            'fonts',
            'FreeSans.ttf')
        try:
            get_and_register_font(
                'FreeSans',
                font_url,
                local_font_path)

        except Exception as e:
            print(f"Ошибка при регистрации шрифта: {e}")
            return HttpResponse("Ошибка регистация шрифта", status=500)

        p.setFont('FreeSans', 12)

        p.drawString(50, 750, 'Список покупок:')
        y = 730
        for recipe in recipes:
            p.drawString(50, y, f'Рецепт: {recipe.name}')
            y -= 20
            ingredients_in_recipe = IngredientInRecipe.objects.filter(
                recipe=recipe).prefetch_related('ingredient')
            for ingredient_in_recipe in ingredients_in_recipe:
                ingredient = ingredient_in_recipe.ingredient
                amount = ingredient_in_recipe.amount
                p.drawString(
                    70, y, f'- {ingredient.name}:'
                           f' {amount} {ingredient.measurement_unit}')
                y -= 15
            y -= 5

        p.showPage()
        p.save()

        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_cart.pdf"'

        return response

    @action(detail=True, methods=['get'], url_path='get-link',
            permission_classes=[AllowAny])
    def get_short_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = generate_short_link(request, recipe.pk)

        return Response({'short_link': short_link},
                        status=status.HTTP_200_OK)


def get_and_register_font(font_name, font_url, local_path):
    """
    Проверяет, существует ли файл шрифта по local_path.
    Если нет, скачивает его с font_url и сохраняет по local_path,
    затем регистрирует шрифт под именем font_name.
    """
    if not os.path.exists(local_path):
        response = requests.get(font_url)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(response.content)
        else:
            raise Exception(
                f"Ошибка скачивания шрифта. "
                f"Код ответа: {response.status_code}")
    pdfmetrics.registerFont(TTFont(font_name, local_path))
