from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.viewsets import GenericViewSet
from blog.errcode import ARTICLE_INFO, PARAM_ERROR, SUCCESS, COMMENT_INFO
from blog.models import Article, Comment
from blog.serializers import ArticleSerializers, CategorySerializers, CommentSerializers, ReplySerializers
from blog.utils import es_search, custom_response, TenPagination, TwentyPagination, CustomAuth, query_combination, \
    QueryException


class ArticleViewSets(GenericViewSet):
    queryset = Article.objects.all()
    authentication_classes = [CustomAuth]
    permission_classes = [IsAuthenticated]
    serializer_class = ArticleSerializers
    pagination_class = TenPagination

    def get_object(self):
        """
        获取models对象
        :return:
        """
        try:
            instance_id = int(self.request.data.pop('id', None))
        except (ValueError, TypeError, AttributeError):
            raise Article.DoesNotExist
        instance = self.queryset.get(
            id=instance_id,
            user=self.request.user
        )
        return instance

    @staticmethod
    def get_category(data, context):
        """
        上下文设置目录
        :param data:
        :param context:
        :return:
        """
        if data.get('category'):
            category = CategorySerializers(data=data)
            category.is_valid(raise_exception=True)
            category = category.save()
            context['category'] = category
        return context

    def list(self, request):
        """
        查看自己的文章
        :param request:
        :return:
        """
        page = self.pagination_class()
        instances = self.queryset.filter(
            user=request.user
        ).order_by('-datetime_created').all()
        page_list = page.paginate_queryset(instances, request, view=self)
        serializers = self.serializer_class(
            instance=page_list,
            many=True
        )
        serializers.child.Meta.fields = ['id', 'title', 'attached_pictures',
                                         'category_name', 'publish_status', 'content',
                                         'tag', 'datetime_created', 'datetime_update']

        declared_fields_list = ['attached_pictures', 'category_name', 'datetime_update',
                                'datetime_created']
        serializers.child._declared_fields = {k: serializers.child._declared_fields[k] for k in declared_fields_list}
        ARTICLE_INFO['data'] = page.get_paginated_data(serializers.data)
        return custom_response(ARTICLE_INFO, 200)

    def create(self, request):
        """
        创建文章
        :param request:
        :return:
        """
        context = {"user": request.user}
        context = self.get_category(request.data, context)

        serializer = self.serializer_class(
            data=request.data,
            context=context,
            meta=2
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return custom_response(SUCCESS, 200)

    def put(self, request):
        """
        修改文章
        :param request:
        :return:
        """
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
            context=context,
            meta=2
        )
        serializer.is_valid(
            raise_exception=True
        )
        serializer.save()

        return custom_response(SUCCESS, 200)

    def delete(self, request):
        """
        删除文章
        :param request:
        :return:
        """
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
        """
        搜索文章
        :param request:
        :return:
        """
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
            many=True,
        )
        serializers.child.Meta.fields = ['id', 'user_info', 'title', 'category_name', 'attached_pictures',
                                         'datetime_created']
        declared_fields_list = ['attached_pictures', 'category_name', 'user_info', 'datetime_created']
        serializers.child._declared_fields = {k: serializers.child._declared_fields[k] for k in declared_fields_list}

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
        """
        查看所有文章
        :param request:
        :return:
        """
        page = self.pagination_class()
        instances = self.queryset.filter(
            publish_status=True
        ).order_by(
            '-datetime_created'
        ).all()
        page_list = page.paginate_queryset(instances, request, view=self)
        serializers = self.serializer_class(
            instance=page_list,
            many=True
        )
        serializers.child.Meta.fields = ['id', 'user_info', 'title', 'category_name', 'attached_pictures',
                                         'datetime_created']
        declared_fields_list = ['attached_pictures', 'category_name', 'user_info', 'datetime_created']
        serializers.child._declared_fields = {k: serializers.child._declared_fields[k] for k in declared_fields_list}

        ARTICLE_INFO['data'] = page.get_paginated_data(serializers.data)
        return custom_response(ARTICLE_INFO, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[AllowAny],
            authentication_classes=[])
    def get_article(self, request):
        """
        查看一篇文章
        :param request:
        :return:
        """
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

        serializer = self.serializer_class(instance=instance, meta=1)
        ARTICLE_INFO['data'] = serializer.data
        return custom_response(ARTICLE_INFO, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[AllowAny],
            authentication_classes=[])
    def query(self, request):
        page = self.pagination_class()
        try:
            filter_objects = query_combination(request.data)
            instances = self.queryset.filter(
                filter_objects
            ).order_by(
                '-datetime_created'
            ).all()
        except (QueryException, ValueError):
            return custom_response(PARAM_ERROR, 200)
        page_list = page.paginate_queryset(instances, request, view=self)
        serializers = self.serializer_class(
            instance=page_list,
            many=True
        )
        serializers.child.Meta.fields = ['id', 'user_info', 'title', 'category_name', 'attached_pictures',
                                         'datetime_created']
        declared_fields_list = ['attached_pictures', 'category_name', 'user_info', 'datetime_created']
        serializers.child._declared_fields = {k: serializers.child._declared_fields[k] for k in declared_fields_list}
        ARTICLE_INFO['data'] = page.get_paginated_data(serializers.data)
        return custom_response(ARTICLE_INFO, 200)


class CommentViewSets(GenericViewSet):
    queryset = Comment.objects.all()
    authentication_classes = [CustomAuth]
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializers
    pagination_class = TwentyPagination

    def list(self, request):
        """
        获得一篇文章的所有评论
        :param request:
        :return:
        """
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
        """
        发表评论
        :param request:
        :return:
        """
        request.data['user_id'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        COMMENT_INFO['data'] = serializer.data
        return custom_response(COMMENT_INFO, 200)

    @staticmethod
    def put(request):
        """
        回复评论
        :param request:
        :return:
        """
        request.data['user_id'] = request.user.id
        serializer = ReplySerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        COMMENT_INFO['data'] = serializer.data
        return custom_response(COMMENT_INFO, 200)

    def delete(self, request):
        """
        删除评论
        :param request:
        :return:
        """
        try:
            comment_id = int(request.data['id'])
        except (KeyError, ValueError, AttributeError):
            return custom_response(PARAM_ERROR, 200)

        self.queryset.filter(
            id=comment_id,
            user_id=request.user.id
        ).delete()

        return custom_response(SUCCESS, 200)
