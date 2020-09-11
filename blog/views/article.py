import uuid
from collections import OrderedDict

from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication
from blog.errcode import ARTICLE_INFO, PARAM_ERROR, SUCCESS, COMMENT_INFO
from blog.models import Article, Comment, Reply
from blog.serializers import ArticleSerializers, CategorySerializers, CommentSerializers, ReplySerializers, \
    ViewArticleSerializers
from blog.utils import search


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
            instance_id = uuid.UUID(self.request.data.pop('id', None))
        except (ValueError, TypeError, AttributeError):
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
        serializers = ViewArticleSerializers(
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

    @action(detail=False,
            methods=['POST'],
            permission_classes=[AllowAny],
            authentication_classes=[])
    def search(self, request):
        try:
            search_keywords = request.data['search_keywords']
            page = int(request.data['page'])
        except (KeyError, ValueError):
            return Response(PARAM_ERROR, 200)
        res_dict, res_count = search.query_search(search_keywords, page, 10)
        article_id_list = []
        for res in res_dict['hits']['hits']:
            article_id_list.append(res['_id'])
        articles = self.queryset.filter(
            id__in=article_id_list
        ).all()
        serializers = self.serializer_class(
            instance=articles,
            many=True
        )

        ARTICLE_INFO['data'] = {
            "results": serializers.data,
            "count": res_count
        }
        return Response(ARTICLE_INFO, 200)

    @action(detail=False,
            methods=['GET'],
            permission_classes=[AllowAny],
            authentication_classes=[])
    def all_article(self, request):
        page = self.pagination_class()
        instances = self.queryset.filter(
            publish_status=True
        ).order_by(
            '-datetime_created'
        ).all()
        page_list = page.paginate_queryset(instances, request, view=self)
        serializers = ViewArticleSerializers(
            instance=page_list,
            many=True
        )

        ARTICLE_INFO['data'] = page.get_paginated_data(serializers.data)
        return Response(ARTICLE_INFO, 200)

    @action(detail=False,
            methods=['GET'],
            permission_classes=[AllowAny],
            authentication_classes=[])
    def get_article(self, request):
        try:
            article_id = uuid.UUID(request.query_params['id'])
        except (KeyError, ValueError, AttributeError):
            return Response(PARAM_ERROR, 200)
        try:
            instance = self.queryset.get(
                id=article_id,
                publish_status=True
            )
        except Article.DoesNotExist:
            return Response(PARAM_ERROR, 200)

        serializers = self.serializer_class(instance=instance)
        ARTICLE_INFO['data'] = serializers.data
        return Response(ARTICLE_INFO, 200)


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
            article_id = uuid.UUID(data['article_id'])
        except (KeyError, ValueError, AttributeError):
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
            comment_id = uuid.UUID(request.data['id'])
        except (KeyError, ValueError, AttributeError):
            return Response(PARAM_ERROR, 200)

        if self.queryset.filter(
                id=comment_id,
                user_id=request.user.id
        ).delete():
            Reply.objects.filter(
                comment_id=request.data['id']
            ).delete()

        return Response(SUCCESS, 200)
