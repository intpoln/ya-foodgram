from django.db.models import Count
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import User

from .serializers import (
    AvatarSerializer,
    SubscriptionSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)


class UserViewSet(DjoserUserViewSet):
    """
    ViewSet для работы с пользователями.

    Реализует следующие эндпоинты:
    - GET /api/users/ - список пользователей
    - POST /api/users/ - регистрация нового пользователя
    - GET /api/users/{id}/ - профиль пользователя
    - GET /api/users/me/ - текущий пользователь
    - POST /api/users/set_password/ - изменение пароля
    - PUT/DELETE /api/users/me/avatar/ - управление аватаром
    - GET /api/users/subscriptions/ - список подписок
    - POST/DELETE /api/users/{id}/subscribe/ - подписка/отписка
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=(IsAuthenticated,),
        url_path="me",
    )
    def me(self, request):
        """Получение информации о текущем пользователе."""
        return super().me(request)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Получение списка подписок текущего пользователя."""
        queryset = (
            User.objects.filter(subscribers__user=request.user)
            .annotate(recipes_count=Count("recipes"))
            .order_by("id")
            .prefetch_related("recipes")
        )

        page = self.paginate_queryset(queryset)
        serializer = UserWithRecipesSerializer(
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=(IsAuthenticated,),
        url_path="subscribe",
    )
    def subscribe(self, request, id=None):
        """Подписка на пользователя."""
        user = request.user
        author = get_object_or_404(User, id=id)
        serializer = SubscriptionSerializer(
            data={"user": user.id, "author": author.id},
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Отписка от автора."""
        author = get_object_or_404(User, id=id)
        deleted_count, _ = request.user.subscriptions.filter(
            author=author
        ).delete()

        if not deleted_count:
            return Response(
                {"errors": "Вы не подписаны на этого автора."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["put"],
        permission_classes=(IsAuthenticated,),
        url_path="me/avatar",
    )
    def set_avatar(self, request):
        """Установка аватара пользователя."""
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @set_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара пользователя."""
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
