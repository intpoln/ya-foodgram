from django.contrib.auth.models import AbstractUser
from django.db import models

NAME_MAX_LENGTH = 150


class User(AbstractUser):
    """Кастомная модель пользователя."""

    email = models.EmailField(
        "Email адрес",
        unique=True,
    )
    first_name = models.CharField(
        "Имя",
        max_length=NAME_MAX_LENGTH,
    )
    last_name = models.CharField(
        "Фамилия",
        max_length=NAME_MAX_LENGTH,
    )
    avatar = models.ImageField(
        "Аватар",
        upload_to="users/",
        blank=True,
        null=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("username", "first_name", "last_name")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписки пользователя на автора."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscribers",
        verbose_name="Автор",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = (
            models.UniqueConstraint(
                fields=("user", "author"), name="unique_subscription"
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("author")),
                name="prevent_self_subscription",
            ),
        )

    def __str__(self):
        return f"{self.user} подписан на {self.author}"
