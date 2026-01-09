from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet,
    RecipeShortLinkRedirectView,
    RecipeViewSet,
    TagViewSet,
)

router = DefaultRouter()
router.register("tags", TagViewSet, basename="tags")
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "recipes-short/<str:short_code>/",
        RecipeShortLinkRedirectView.as_view(),
        name="recipe-short-link-redirect",
    ),
]
