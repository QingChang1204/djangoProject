from collections import OrderedDict
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication
from blog.errcode import ARTICLE_INFO
from blog.models import Article
from blog.serializers import ArticleSerializers


class ArticlePagination(PageNumberPagination):
    page_size = 10

    def get_paginated_data(self, data):
        return OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ])


class ArticleViewSets(GenericViewSet):
    queryset = Article.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ArticleSerializers
    pagination_class = ArticlePagination

    def list(self, request):
        page = self.pagination_class()
        articles = self.queryset.filter(
            user_id=request.user.id
        ).order_by('-datetime_created').all()
        page_list = page.paginate_queryset(articles, request, view=self)
        serializers = self.serializer_class(instance=page_list, many=True)

        ARTICLE_INFO['data'] = page.get_paginated_data(serializers.data)
        return Response(ARTICLE_INFO, 200)

    def create(self, request):
        # 序列化器通过上下文兼容外键关系
        article = self.serializer_class(data=request.data, context={"user_id": request.user.id})
        article.is_valid(raise_exception=True)
        article.save()

        ARTICLE_INFO['data'] = article.data
        return Response(ARTICLE_INFO, 200)
