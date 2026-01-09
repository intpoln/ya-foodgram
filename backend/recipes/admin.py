from django.contrib import admin

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)


class IngredientInRecipeInline(admin.TabularInline):
    """Инлайн для ингредиентов в рецепте."""

    model = IngredientInRecipe
    extra = 1
    min_num = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для тегов."""

    list_display = (
        "id",
        "name",
        "slug",
        "get_recipes_count",
    )
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

    def get_recipes_count(self, obj):
        """Количество рецептов с этим тегом."""
        return obj.recipes.count()

    get_recipes_count.short_description = "Рецептов"


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов."""

    list_display = (
        "id",
        "name",
        "measurement_unit",
        "get_recipes_count",
    )
    list_filter = ("measurement_unit",)
    search_fields = ("name",)

    def get_recipes_count(self, obj):
        """Количество рецептов с этим ингредиентом."""
        return obj.recipes.count()

    get_recipes_count.short_description = "Рецептов"


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""

    list_display = (
        "id",
        "name",
        "author",
        "cooking_time",
        "get_tags_display",
        "get_favorites_count",
        "pub_date",
    )
    list_filter = (
        "tags",
        "author",
        "pub_date",
    )
    search_fields = (
        "name",
        "author__username",
        "author__email",
        "text",
    )
    inlines = [IngredientInRecipeInline]
    readonly_fields = (
        "pub_date",
        "get_favorites_count",
        "get_shopping_cart_count",
    )
    filter_horizontal = ("tags",)

    def get_favorites_count(self, obj):
        """Количество добавлений в избранное."""
        return obj.favorites.count()

    get_favorites_count.short_description = "В избранном"

    def get_shopping_cart_count(self, obj):
        """Количество добавлений в список покупок."""
        return obj.shopping_cart.count()

    get_shopping_cart_count.short_description = "В списке покупок"

    def get_tags_display(self, obj):
        """Отображение тегов через запятую."""
        return ", ".join(obj.tags.values_list("name", flat=True))

    get_tags_display.short_description = "Теги"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для избранного."""

    list_display = (
        "id",
        "user",
        "recipe",
        "recipe__author",
    )
    list_filter = (
        "user",
        "recipe",
    )
    search_fields = (
        "user__username",
        "user__email",
        "recipe__name",
    )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для списка покупок."""

    list_display = (
        "id",
        "user",
        "recipe",
        "recipe__author",
    )
    list_filter = (
        "user",
        "recipe",
    )
    search_fields = (
        "user__username",
        "user__email",
        "recipe__name",
    )
