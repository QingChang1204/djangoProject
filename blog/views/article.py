from collections import OrderedDict
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication
from blog.errcode import ARTICLE_INFO, PARAM_ERROR, SUCCESS, COMMENT_INFO
from blog.models import Article, Comment, Reply
from blog.serializers import ArticleSerializers, CategorySerializers, CommentSerializers, ReplySerializers


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

    def get_object(self):
        try:
            instance_id = int(self.request.data.pop('id', None))
        except (ValueError, TypeError):
            raise Article.DoesNotExist
        instance = self.queryset.get(
            id=instance_id,
            user_id=self.request.user.id
        )
        return instance

    def list(self, request):
        page = self.pagination_class()
        articles = self.queryset.filter(
            user_id=request.user.id
        ).order_by('-datetime_created').all()
        page_list = page.paginate_queryset(articles, request, view=self)
        serializers = self.serializer_class(
            instance=page_list,
            many=True
        )

        ARTICLE_INFO['data'] = page.get_paginated_data(serializers.data)
        return Response(ARTICLE_INFO, 200)

    def create(self, request):
        # 序列化器通过上下文兼容外键关系
        category = CategorySerializers(data=request.data)
        category.is_valid(raise_exception=True)
        category = category.save()

        article = self.serializer_class(
            data=request.data,
            context={
                "user_id": request.user.id,
                "category_id": category.id
            })
        article.is_valid(raise_exception=True)
        article.save()

        ARTICLE_INFO['data'] = article.data
        return Response(ARTICLE_INFO, 200)

    def put(self, request):
        try:
            article = self.get_object()
        except Article.DoesNotExist:
            return Response(PARAM_ERROR)
        serializer = self.serializer_class(
            data=request.data,
            instance=article,
            partial=True
        )
        serializer.is_valid(
            raise_exception=True
        )
        serializer.save()

        ARTICLE_INFO['data'] = serializer.data
        return Response(ARTICLE_INFO, 200)

    def delete(self, request):
        try:
            article = self.get_object()
        except Article.DoesNotExist:
            return Response(PARAM_ERROR)

        article.delete()
        return Response(SUCCESS, 200)


class CommentPagination(PageNumberPagination):
    page_size = 20

    def get_paginated_data(self, data):
        return OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ])


class CommentViewSets(GenericViewSet):
    queryset = Comment.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializers
    pagination_class = CommentPagination

    def list(self, request):
        data = request.query_params
        try:
            article_id = int(data['article_id'])
        except (KeyError, ValueError):
            return Response(PARAM_ERROR, 200)
        page = self.pagination_class()
        comments = self.queryset.filter(
            article_id=article_id
        ).order_by('-datetime_created').all()
        page_list = page.paginate_queryset(comments, request, view=self)
        serializers = self.serializer_class(
            instance=page_list,
            many=True
        )

        COMMENT_INFO['data'] = page.get_paginated_data(serializers.data)
        return Response(COMMENT_INFO, 200)

    def create(self, request):
        request.data['user_id'] = request.user.id
        serializers = self.serializer_class(data=request.data)
        serializers.is_valid(raise_exception=True)
        serializers.save()

        COMMENT_INFO['data'] = serializers.data
        return Response(COMMENT_INFO, 200)

    @staticmethod
    def put(request):
        request.data['user_id'] = request.user.id
        serializers = ReplySerializers(data=request.data)
        serializers.is_valid(raise_exception=True)
        serializers.save()

        COMMENT_INFO['data'] = serializers.data
        return Response(COMMENT_INFO, 200)

    def delete(self, request):
        try:
            comment_id = int(request.data['id'])
        except (KeyError, ValueError):
            return Response(PARAM_ERROR, 200)

        if self.queryset.filter(
            id=comment_id,
            user_id=request.user.id
        ).delete():
            Reply.objects.filter(
                comment_id=request.data['id']
            ).delete()

        return Response(SUCCESS, 200)
