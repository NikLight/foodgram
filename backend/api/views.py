from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as DjoserViewSet
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly, AllowAny)
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ReadOnlyModelViewSet

from .filters import RecipeFilter
from .serializers import CustomUserSerializer, Base64ImageField
from .pagination import CustomPagination

from recipes.models import (Recipe,
                            Tag,
                            Ingredient)
from .serializers import (RecipeSerializer,
                          TagSerializer,
                          IngredientSerializer)

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


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

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
