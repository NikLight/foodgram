from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

app_name = 'api'

router = DefaultRouter()

router.register(r'users', UserViewSet,
                basename='users')
router.register(r'recipes', RecipeViewSet,
                basename='recipe')
router.register(r'tags', TagViewSet,
                basename='tag')
router.register(r'ingredients', IngredientViewSet,
                basename='ingredient')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
