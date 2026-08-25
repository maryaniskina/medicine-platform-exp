from typing import Any, cast

from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.serializers import (
    LoginSerializer,
    ProfileUpdateSerializer,
    RegistrationSerializer,
    UserSerializer,
)


@extend_schema(
    tags=['Accounts'],
    summary='Получить CSRF-токен',
    responses={
        200: OpenApiResponse(
            description='CSRF-токен получен и установлен в cookie.',
        ),
    },
)
@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        token = get_token(request)
        response = Response({'csrfToken': token})
        response['Cache-Control'] = 'no-store'
        return response


@extend_schema(
    tags=['Accounts'],
    summary='Зарегистрировать пользователя',
    request=RegistrationSerializer,
    responses={
        201: UserSerializer,
        400: OpenApiResponse(
            description='Ошибка валидации данных.',
        ),
    },
)
@method_decorator(csrf_protect, name='dispatch')
class RegistrationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=['Accounts'],
    summary='Войти в аккаунт',
    request=LoginSerializer,
    responses={
        200: UserSerializer,
        400: OpenApiResponse(
            description='Неверные данные или неактивный аккаунт.',
        ),
    },
)
@method_decorator(csrf_protect, name='dispatch')
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        validated_data = cast(
            dict[str, Any],
            serializer.validated_data,
        )
        user = cast(User, validated_data['user'])
        login(request, user)

        return Response(UserSerializer(user).data)


@extend_schema(
    tags=['Accounts'],
    summary='Выйти из аккаунта',
    request=None,
    responses={
        204: OpenApiResponse(description='Выход выполнен.'),
        403: OpenApiResponse(
            description='Требуется авторизация или CSRF-токен.',
        ),
    },
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=['Accounts'],
    summary='Получить профиль текущего пользователя',
    responses={
        200: UserSerializer,
        403: OpenApiResponse(description='Требуется авторизация.'),
    },
)
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        summary='Обновить профиль текущего пользователя',
        request=ProfileUpdateSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(
                description='Ошибка валидации данных.',
            ),
            403: OpenApiResponse(
                description='Требуется авторизация или CSRF-токен.',
            ),
        },
    )
    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(UserSerializer(user).data)
