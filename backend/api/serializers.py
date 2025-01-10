from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, EmailValidator
from djoser.serializers import UserCreateSerializer as DjoserSerializer, UserSerializer
from rest_framework import serializers

from recipes.constants import (MAX_LENGTH_ROLE,
                               USERNAME_SEARCH_REGEX,
                               MAX_LENGTH_EMAIL)

User = get_user_model()


class UserCreateSerializer(DjoserSerializer):
    username = serializers.CharField(
        max_length=MAX_LENGTH_ROLE,
        validators=[
            RegexValidator(
                regex=USERNAME_SEARCH_REGEX,
                message='Имя пользователя может содержать только буквы,'
                        ' цифры и символы: @/./+/-/_'
            )
        ]
    )
    email = serializers.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        validators=[EmailValidator(message='Некорректный email-адрес.')]
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')


class CustomUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name')
