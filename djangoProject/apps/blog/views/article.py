from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.viewsets import GenericViewSet
from blog.errcode import ARTICLE_INFO, PARAM_ERROR, SUCCESS, COMMENT_INFO
from blog.models import Article, Comment
from blog.serializers import ArticleSerializers, CategorySerializers, CommentSerializers, ReplySerializers, \
    SimpleArticleSerializers, MyArticleSerializers
from blog.utils import es_search, custom_response, TenPagination, TwentyPagination, CustomAuth


class ArticleViewSets(GenericViewSet):
    queryset = Article.objects.all()
    authentication_classes = [CustomAuth]
    permission_classes = [IsAuthenticated]
    serializer_class = ArticleSerializers
    pagination_class = TenPagination

    def get_object(self):
        try:
            instance_id = int(self.request.data.pop('id', None))
        except (ValueError, TypeError, AttributeError):
            raise Article.DoesNotExist
        instance = self.queryset.get(
            id=instance_id,
            user_id=self.request.user.id
        )
        return instance

    @staticmethod
    def get_category(data, context):
        if data.get('category'):
            category = CategorySerializers(data=data)
            category.is_valid(raise_exception=True)
            category = category.save()
            context['category'] = category
        return context

    def list(self, request):
        page = self.pagination_class()
        instances = self.queryset.filter(
            user_id=request.user.id
        ).order_by('-datetime_created').all()
        page_list = page.paginate_queryset(instances, request, view=self)
        serializers = MyArticleSerializers(
            instance=page_list,
            many=True
        )

        ARTICLE_INFO['data'] = page.get_paginated_data(serializers.data)
        return custom_response(ARTICLE_INFO, 200)

    def create(self, request):
        # 序列化器通过上下文兼容外键关系
        context = {"user": request.user}
        context = self.get_category(request.data, context)

        serializer = self.serializer_class(
            data=request.data,
            context=context
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return custom_response(SUCCESS, 200)

    def put(self, request):
        try:
            article = self.get_object()
        except Article.DoesNotExist:
            return custom_response(PARAM_ERROR, 200)
        context = {}
        context = self.get_category(request.data, context)

        serializer = self.serializer_class(
            data=request.data,
            instance=article,
            partial=True,
            context=context
        )
        serializer.is_valid(
            raise_exception=True
        )
        serializer.save()

        return custom_response(SUCCESS, 200)

    def delete(self, request):
        try:
            article = self.get_object()
        except Article.DoesNotExist:
            return custom_response(PARAM_ERROR, 200)
        article.delete()

        return custom_response(SUCCESS, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[AllowAny],
            authentication_classes=[])
    def search(self, request):
        try:
            search_keywords = request.data['search_keywords']
            page = int(request.data['page'])
        except (KeyError, ValueError):
            return custom_response(PARAM_ERROR, 200)
        res_dict, res_count = es_search.query_search(search_keywords, page, 10)
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
        return custom_response(ARTICLE_INFO, 200)

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
        serializers = SimpleArticleSerializers(
            instance=page_list,
            many=True
        )

        ARTICLE_INFO['data'] = page.get_paginated_data(serializers.data)
        return custom_response(ARTICLE_INFO, 200)

    @action(detail=False,
            methods=['GET'],
            permission_classes=[AllowAny],
            authentication_classes=[])
    def get_article(self, request):
        try:
            article_id = int(request.query_params['id'])
        except (KeyError, ValueError, AttributeError):
            return custom_response(PARAM_ERROR, 200)
        try:
            instance = self.queryset.get(
                id=article_id,
                publish_status=True
            )
        except Article.DoesNotExist:
            return custom_response(PARAM_ERROR, 200)

        serializer = self.serializer_class(instance=instance)
        ARTICLE_INFO['data'] = serializer.data
        return custom_response(ARTICLE_INFO, 200)


class CommentViewSets(GenericViewSet):
    queryset = Comment.objects.all()
    authentication_classes = [CustomAuth]
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializers
    pagination_class = TwentyPagination

    def list(self, request):
        try:
            article_id = request.query_params['id']
        except (KeyError, ValueError):
            return custom_response(PARAM_ERROR, 200)
        instance = self.queryset.filter(
            article_id=article_id
        ).all()
        serializers = self.serializer_class(
            instance=instance,
            many=True
        )

        COMMENT_INFO['data'] = serializers.data
        return custom_response(COMMENT_INFO, 200)

    def create(self, request):
        request.data['user_id'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        COMMENT_INFO['data'] = serializer.data
        return custom_response(COMMENT_INFO, 200)

    @staticmethod
    def put(request):
        request.data['user_id'] = request.user.id
        serializer = ReplySerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        COMMENT_INFO['data'] = serializer.data
        return custom_response(COMMENT_INFO, 200)

    def delete(self, request):
        try:
            comment_id = int(request.data['id'])
        except (KeyError, ValueError, AttributeError):
            return custom_response(PARAM_ERROR, 200)

        self.queryset.filter(
            id=comment_id,
            user_id=request.user.id
        ).delete()

        return custom_response(SUCCESS, 200)
