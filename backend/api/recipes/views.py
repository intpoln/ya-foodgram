from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from recipes.utils import generate_shopping_list

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    FavoriteCreateSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeSerializer,
    ShoppingCartCreateSerializer,
    TagSerializer,
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с тегами рецептов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["^name"]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""

    queryset = Recipe.objects.select_related("author").prefetch_related(
        "tags",
        "ingredient_amounts__ingredient",
    )
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action in ["create", "partial_update"]:
            return RecipeCreateSerializer
        return RecipeSerializer

    @action(
        detail=True,
        methods=["post"],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        get_object_or_404(Recipe, pk=pk)
        serializer = FavoriteCreateSerializer(
            data={"recipe": pk}, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        get_object_or_404(Recipe, pk=pk)
        deleted, _ = Favorite.objects.filter(
            user=request.user, recipe_id=pk
        ).delete()
        if not deleted:
            return Response(
                {"errors": "Рецепт не в избранном."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=(IsAuthenticated,),
        url_path="shopping_cart",
    )
    def shopping_cart(self, request, pk=None):
        get_object_or_404(Recipe, pk=pk)
        serializer = ShoppingCartCreateSerializer(
            data={"recipe": pk}, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        get_object_or_404(Recipe, pk=pk)
        deleted, _ = ShoppingCart.objects.filter(
            user=request.user, recipe_id=pk
        ).delete()
        if not deleted:
            return Response(
                {"errors": "Рецепт не в списке покупок."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=(IsAuthenticated,),
        url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок в формате TXT."""
        shopping_list = generate_shopping_list(request.user)

        response = HttpResponse(
            shopping_list, content_type="text/plain; charset=utf-8"
        )
        response["Content-Disposition"] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=True,
        methods=["get"],
        url_path="get-link",
    )
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk)
        base_url = request.build_absolute_uri("/")
        short_link = f"{base_url}r/{recipe.short_code}/"
        return Response({"short-link": short_link})


class RecipeShortLinkRedirectView(APIView):

    def get(self, request, short_code):
        recipe = get_object_or_404(Recipe, short_code=short_code)
        base_url = request.build_absolute_uri("/")
        redirect_url = f"{base_url}recipes/{recipe.id}/"
        return HttpResponseRedirect(redirect_url)
