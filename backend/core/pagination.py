from rest_framework.pagination import PageNumberPagination

DEFAULT_PAGE_SIZE = 6


class PageNumberPagination(PageNumberPagination):
    """Пагинатор с параметром limit."""

    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = "limit"
