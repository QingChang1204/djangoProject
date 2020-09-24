from rest_framework.pagination import PageNumberPagination

from blog.mixin import PaginationMixin


class TenPagination(PageNumberPagination, PaginationMixin):
    page_size = 10


class TwentyPagination(PageNumberPagination, PaginationMixin):
    page_size = 20
