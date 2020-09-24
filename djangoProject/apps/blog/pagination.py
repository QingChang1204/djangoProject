from rest_framework.pagination import PageNumberPagination
from collections import OrderedDict


class PaginationMixin:
    def get_paginated_data(self, data):
        return OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ])


class TenPagination(PageNumberPagination, PaginationMixin):
    page_size = 10


class TwentyPagination(PageNumberPagination, PaginationMixin):
    page_size = 20
