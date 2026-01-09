from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import Subscription, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка для пользователей."""

    list_display = (
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "get_recipes_count",
    )
    list_filter = (
        "email",
        "username",
        "is_staff",
        "is_superuser",
    )
    search_fields = (
        "email",
        "username",
        "first_name",
        "last_name",
    )
    readonly_fields = ("date_joined", "last_login")

    def get_recipes_count(self, obj):
        """Количество рецептов пользователя."""
        return obj.recipes.count()

    get_recipes_count.short_description = "Рецептов"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка для подписок."""

    list_display = (
        "id",
        "user",
        "author",
        "get_author_recipes_count",
    )
    list_filter = (
        "user",
        "author",
    )
    search_fields = (
        "user__username",
        "user__email",
        "author__username",
        "author__email",
    )

    def get_author_recipes_count(self, obj):
        """Количество рецептов автора."""
        return obj.author.recipes.count()

    get_author_recipes_count.short_description = "Рецептов у автора"
