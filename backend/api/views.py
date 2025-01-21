from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserViewSet
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly, AllowAny)
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ReadOnlyModelViewSet

from .filters import RecipeFilter
from .pagination import CustomPagination

from recipes.models import (Recipe,
                            Tag,
                            Ingredient, Subscription)
from .serializers import (CustomUserSerializer,
                          Base64ImageField,
                          RecipeSerializer,
                          TagSerializer,
                          IngredientSerializer,
                          SubscriptionUserSerializer, RecipeShortSerializer)

User = get_user_model()


class UserViewSet(DjoserViewSet):
    queryset = User.objects.all().order_by('id')
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar', permission_classes=[IsAuthenticated])
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            avatar = request.data.get('avatar')
            if avatar:
                try:
                    user.avatar = Base64ImageField().to_internal_value(avatar)
                    user.save()
                    serializer = CustomUserSerializer(user)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                except ValidationError as e:
                    return Response({"detail": str(e)},
                                    status=status.HTTP_400_BAD_REQUEST)
            return Response(
                {"detail": "Файл 'avatar' не найден."},
                status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            user.avatar.delete(save=True)
            user.save()
            serializer = CustomUserSerializer(user)
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='subscriptions', permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(user=user).select_related('author')
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
            authors_for_subscriptions, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe', permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        """Позволяет подписываться и отписываться от пользователей."""
        user = request.user
        author = get_object_or_404(User, pk=id)

        if user == author:
            return Response(
                {"detail": "Нельзя подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {"detail": "Вы уже подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=user, author=author)

            recipes_limit = request.query_params.get('recipes_limit', None)
            recipes = Recipe.objects.filter(author=author)
            if recipes_limit:
                try:
                    recipes_limit = int(recipes_limit)
                    recipes = recipes[:recipes_limit]
                except ValueError:
                    return Response(
                        {"detail": "Неверное значение параметра 'recipes_limit'."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            serializer = SubscriptionUserSerializer(
                author, context={'request': request})
            response_data = serializer.data
            response_data['recipes'] = RecipeShortSerializer(recipes, many=True).data

            return Response(response_data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            subscription = Subscription.objects.filter(user=user, author=author).first()
            if not subscription:
                return Response(
                    {"detail": "Вы не подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(
                {"detail": "Вы успешно отписались."},
                status=status.HTTP_204_NO_CONTENT
            )



class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        query = self.request.query_params.get('name', None)

        if query:
            results_start = Ingredient.objects.filter(
                name__istartswith=query)
            results_contains = Ingredient.objects.filter(
                name__icontains=query).exclude(
                name__istartswith=query)
            results = results_start | results_contains

            return results.order_by('name')

        return Ingredient.objects.all().order_by('name')


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination

    filterset_class = RecipeFilter

    def get_queryset(self):
        return Recipe.objects.all().order_by('-pub_date')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
