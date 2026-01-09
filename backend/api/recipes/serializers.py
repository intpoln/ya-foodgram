from rest_framework import serializers

from api.users.serializers import UserSerializer
from core.fields import Base64ImageField
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тега."""

    class Meta:
        model = Tag
        fields = (
            "id",
            "name",
            "slug",
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиента."""

    class Meta:
        model = Ingredient
        fields = (
            "id",
            "name",
            "measurement_unit",
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиента в рецепте."""

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            "id",
            "name",
            "measurement_unit",
            "amount",
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецепта."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source="ingredient_amounts",
        many=True,
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        """Проверка, находится ли рецепт в избранном пользователя."""
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and Favorite.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Проверка, находится ли рецепт в списке покупок пользователя."""
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and ShoppingCart.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        )


class RecipeRelationSerializer(serializers.ModelSerializer):
    """Сериализатор для связи между пользователем и рецептом."""

    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        fields = ("user", "recipe")
        read_only_fields = ("user",)

    def validate(self, attrs):
        user = self.context.get("request").user
        recipe = attrs.get("recipe")
        if self.Meta.model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                "Рецепт уже в списке покупок."
            )
        return attrs

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe, context=self.context
        ).data


class FavoriteCreateSerializer(RecipeRelationSerializer):
    """Сериализатор для создания избранного."""

    class Meta(RecipeRelationSerializer.Meta):
        model = Favorite


class ShoppingCartCreateSerializer(RecipeRelationSerializer):
    """Сериализатор для создания списка покупок."""

    class Meta(RecipeRelationSerializer.Meta):
        model = ShoppingCart


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания ингредиента в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        source="ingredient",
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            "id",
            "amount",
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""

    ingredients = IngredientInRecipeCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
        )

    def validate(self, attrs):
        """Валидация на уровне объекта."""
        ingredients = attrs.get("ingredients")
        tags = attrs.get("tags")

        if not ingredients:
            raise serializers.ValidationError(
                {"ingredients": "Добавьте хотя бы один ингредиент."}
            )

        ingredient_ids = [
            ingredient_data["ingredient"].id
            for ingredient_data in ingredients
        ]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {"ingredients": "Ингредиенты не должны повторяться."}
            )

        if not tags:
            raise serializers.ValidationError(
                {"tags": "Добавьте хотя бы один тег."}
            )

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {"tags": "Теги не должны повторяться."}
            )
        return attrs

    def validate_image(self, value):
        """Валидация изображения."""
        if self.instance is None and not value:
            raise serializers.ValidationError(
                {"image": "Добавьте изображение."}
            )
        return value

    @staticmethod
    def create_ingredients(recipe, ingredients):
        """Создание связей ингредиентов с рецептом."""
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                ingredient_id=ingredient_data["ingredient"].id,
                amount=ingredient_data["amount"],
            )
            for ingredient_data in ingredients
        ])

    def create(self, validated_data):
        """Создание нового рецепта."""
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")

        request = self.context.get("request")
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта."""
        ingredients = validated_data.pop("ingredients", None)
        tags = validated_data.pop("tags", None)

        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.ingredient_amounts.all().delete()
        self.create_ingredients(instance, ingredients)
        return instance

    def to_representation(self, instance):
        """Возврат сериализованного рецепта после создания."""
        return RecipeSerializer(instance, context=self.context).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор рецепта."""

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
        )
