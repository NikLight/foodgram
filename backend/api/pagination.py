from rest_framework.pagination import PageNumberPagination
from recipes.constants import PAGE_SIZE, MAX_PAGE_SIZE


class CustomPagination(PageNumberPagination):
    page_size = PAGE_SIZE
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGE_SIZE
