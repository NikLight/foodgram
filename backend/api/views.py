from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as DjoserViewSet
from rest_framework import status
from rest_framework.response import Response

from .serializers import CustomUserSerializer

User = get_user_model()


class UserViewSet(DjoserViewSet):
    queryset = User.objects.all()
    pagination_class = 'rest_framework.pagination.PageNumberPagination'

    def me(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)










