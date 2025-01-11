from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as DjoserViewSet
from rest_framework import status, viewsets
from rest_framework.response import Response
from .serializers import CustomUserSerializer
from .pagination import CustomPagination

from recipes.models import (Recipe,
                            Tag, Ingredient)
from .serializers import (RecipeSerializer,
                          TagSerializer,
                          IngredientSerializer)

User = get_user_model()


class UserViewSet(DjoserViewSet):
    queryset = User.objects.all().order_by('id')
    pagination_class = CustomPagination

    def me(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
