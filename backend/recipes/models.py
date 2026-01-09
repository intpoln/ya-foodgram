import secrets
import string

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User

TAG_NAME_MAX_LENGTH = 32
TAG_SLUG_MAX_LENGTH = 32
INGREDIENT_NAME_MAX_LENGTH = 128
MEASUREMENT_UNIT_MAX_LENGTH = 64
RECIPE_NAME_MAX_LENGTH = 256
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 32000
MIN_INGREDIENT_AMOUNT = 1
MAX_INGREDIENT_AMOUNT = 32000
SHORT_CODE_LENGTH = 6


class Tag(models.Model):
    """Модель тега рецепта."""

    name = models.CharField(
        "Название",
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
    )
    slug = models.SlugField(
        "Slug",
        max_length=TAG_SLUG_MAX_LENGTH,
        unique=True,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        "Название",
        max_length=INGREDIENT_NAME_MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        "Единица измерения",
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("name",)
        models.UniqueConstraint(
            fields=("name", "measurement_unit"), name="unique_ingredient"
        )

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    name = models.CharField(
        "Название",
        max_length=RECIPE_NAME_MAX_LENGTH,
    )
    image = models.ImageField(
        "Картинка",
        upload_to="recipes/images/",
    )
    text = models.TextField(
        "Описание",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="IngredientInRecipe",
        related_name="recipes",
        verbose_name="Ингредиенты",
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="recipes",
        verbose_name="Теги",
    )
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления (в минутах)",
        validators=(
            MinValueValidator(
                MIN_COOKING_TIME,
                message="Время приготовления не может быть меньше "
                        f"{MIN_COOKING_TIME} минуты.",
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message="Время приготовления не может превышать "
                        f"{MAX_COOKING_TIME} минут.",
            ),
        ),
    )
    pub_date = models.DateTimeField(
        "Дата публикации",
        auto_now_add=True,
    )

    short_code = models.CharField(
        "Короткая ссылка",
        max_length=SHORT_CODE_LENGTH,
        unique=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-pub_date",)

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = self.generate_short_code()
        super().save(*args, **kwargs)

    def generate_short_code(self):
        alphabet = string.ascii_letters + string.digits
        while True:
            code = "".join(
                secrets.choice(alphabet) for _ in range(SHORT_CODE_LENGTH)
            )
            if not Recipe.objects.filter(short_code=code).exists():
                return code

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Промежуточная модель для связи рецепта и ингредиента."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredient_amounts",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredient_amounts",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        "Количество",
        validators=(
            MinValueValidator(
                MIN_INGREDIENT_AMOUNT,
                message="Количество ингредиента не может быть меньше "
                        f"{MIN_INGREDIENT_AMOUNT}.",
            ),
            MaxValueValidator(
                MAX_INGREDIENT_AMOUNT,
                message="Количество ингредиента не может превышать "
                        f"{MAX_INGREDIENT_AMOUNT}.",
            ),
        ),
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        constraints = (
            models.UniqueConstraint(
                fields=("recipe", "ingredient"),
                name="unique_ingredient_in_recipe",
            ),
        )

    def __str__(self):
        return f"{self.recipe.name} - {self.ingredient.name}: {self.amount}"


class Favorite(models.Model):
    """Модель избранного рецепта."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = (
            models.UniqueConstraint(
                fields=("user", "recipe"), name="unique_favorite"
            ),
        )

    def __str__(self):
        return f"{self.user} добавил в избранное {self.recipe}"


class ShoppingCart(models.Model):
    """Модель списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        constraints = (
            models.UniqueConstraint(
                fields=("user", "recipe"), name="unique_shopping_cart"
            ),
        )

    def __str__(self):
        return f"{self.user} добавил в список покупок {self.recipe}"
