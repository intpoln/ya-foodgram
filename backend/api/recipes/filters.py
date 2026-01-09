from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов по тегам и автору."""

    tags = filters.AllValuesMultipleFilter(field_name="tags__slug")
    author = filters.NumberFilter(field_name="author__id")
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = ("tags", "author")

    def filter_is_favorited(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if user is None or user.is_anonymous:
            return queryset.none() if value else queryset
        if value:
            return queryset.filter(favorites__user=user)
        return queryset.exclude(favorites__user=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if user is None or user.is_anonymous:
            return queryset.none() if value else queryset
        if value:
            return queryset.filter(shopping_cart__user=user)
        return queryset.exclude(shopping_cart__user=user)

    def _parse_tags_value(self, value):
        """Парсинг значения тегов из различных форматов."""
        if isinstance(value, str):
            return [tag.strip() for tag in value.split(",") if tag.strip()]
        if isinstance(value, list):
            return [tag.strip() for tag in value if tag.strip()]
        return [str(value).strip()] if value else []

    def _normalize_tags(self, tags_params):
        """Нормализация списка тегов: удаление пустых значений и дубликатов."""
        return list(set(tag.strip() for tag in tags_params if tag.strip()))

    def _are_all_tags_selected(self, selected_tags):
        """Проверка, выбраны ли все доступные теги."""
        all_tags_slugs = set(Tag.objects.values_list("slug", flat=True))
        selected_tags_slugs = set(selected_tags)
        return (
            selected_tags_slugs == all_tags_slugs and len(all_tags_slugs) > 0
        )


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов по началу названия."""

    name = filters.CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)
