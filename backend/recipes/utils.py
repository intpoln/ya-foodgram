from django.db.models import F, Sum

from recipes.models import Recipe


def generate_shopping_list(user) -> str:
    """Генерация списка покупок для пользователя."""

    ingredients = (
        Recipe.objects.filter(shopping_cart__user=user)
        .values(
            ingredient_name=F("ingredient_amounts__ingredient__name"),
            ingredient_unit=F(
                "ingredient_amounts__ingredient__measurement_unit"
            ),
        )
        .annotate(total=Sum("ingredient_amounts__amount"))
        .order_by("ingredient_name", "ingredient_unit")
    )

    shopping_list = [
        f"{item['ingredient_name']} "
        f"({item['ingredient_unit']}) — {item['total']}"
        for item in ingredients
    ]
    return "\n".join(shopping_list)
