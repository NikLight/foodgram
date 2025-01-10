from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

app_name = 'api'

v1_router = DefaultRouter()

v1_router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(v1_router.urls)),
]

