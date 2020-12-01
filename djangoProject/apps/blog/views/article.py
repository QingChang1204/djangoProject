from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.viewsets import GenericViewSet
from blog.errcode import ARTICLE_INFO, PARAM_ERROR, SUCCESS, COMMENT_INFO, MUST_LOG_IN
from blog.models import Article, Comment, Reply
from blog.serializers import ArticleSerializers, CategorySerializers, CommentSerializers, ReplySerializers, \
    SimpleArticleSerializer, CommonArticleSerializer, SimpleArticleUserSerializer
from blog.utils import es_search, custom_response, TenPagination, TwentyPagination, CustomAuth, query_combination, \
    QueryException


class ArticleViewSets(GenericViewSet):
    queryset = Article.objects.all()
    authentication_classes = [CustomAuth]
    permission_classes = [IsAuthenticated]
    serializer_class = ArticleSerializers
    pagination_class = TenPagination

    def get_article(self, request):
        """
        获取models对象
        :return:
        """
        try:
            instance_id = int(request.data.pop('id', None))
        except (ValueError, TypeError, AttributeError):
            raise Article.DoesNotExist
        else:
            instance = self.queryset.only('id').get(
                id=instance_id,
                user=request.user
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
        page = self.paginator
        instances = SimpleArticleSerializer.get_instance().order_by('-datetime_created').all()
        page_list = page.paginate_queryset(instances, request, view=self)
        serializers = SimpleArticleSerializer(
            instance=page_list,
            many=True
        )
        ARTICLE_INFO['data'] = page.get_paginated_data(serializers.data)

        return custom_response(ARTICLE_INFO, 200)

    def create(self, request):
        """
        创建文章
        :param request:
        :return:
        """
        context = self.get_category(request.data, {"user": request.user})
        serializer = CommonArticleSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(**context)

        return custom_response(SUCCESS, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[IsAuthenticated],
            authentication_classes=[CustomAuth])
    def update_article(self, request):
        """
        修改文章
        :param request:
        :return:
        """
        try:
            article = self.get_article(request)
        except Article.DoesNotExist:
            return custom_response(PARAM_ERROR, 200)
        else:
            context = self.get_category(request.data, {"user": request.user})
            serializer = CommonArticleSerializer(
                data=request.data,
                instance=article,
                partial=True,
            )
            serializer.is_valid(
                raise_exception=True
            )
            serializer.save(**context)

        return custom_response(SUCCESS, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[IsAuthenticated],
            authentication_classes=[CustomAuth])
    def delete_article(self, request):
        """
        删除文章
        :param request:
        :return:
        """
        try:
            article = self.get_article(request)
        except Article.DoesNotExist:
            return custom_response(PARAM_ERROR, 200)
        else:
            article.delete()

        return custom_response(SUCCESS, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[AllowAny | IsAuthenticated],
            authentication_classes=[CustomAuth])
    def search_article(self, request):
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
        else:
            res_dict, res_count = es_search.query_search(search_keywords, page, 10)
            article_id_list = []
            for res in res_dict['hits']['hits']:
                article_id_list.append(res['_id'])

            articles = SimpleArticleUserSerializer.get_instance().filter(
                id__in=article_id_list
            ).all()
            serializers = SimpleArticleUserSerializer(
                instance=articles,
                many=True,
            )

            ARTICLE_INFO['data'] = {
                "results": serializers.data,
                "count": res_count
            }

        return custom_response(ARTICLE_INFO, 200)

    @action(detail=False,
            methods=['GET'],
            permission_classes=[AllowAny | IsAuthenticated],
            authentication_classes=[CustomAuth])
    def all_article_info(self, request):
        """
        查看所有文章
        :param request:
        :return:
        """
        page = self.paginator
        instances = SimpleArticleUserSerializer.get_instance().filter(
            publish_status=True
        ).order_by(
            '-datetime_created'
        ).all()
        page_list = page.paginate_queryset(instances, request, view=self)
        serializers = SimpleArticleUserSerializer(
            instance=page_list,
            many=True
        )
        ARTICLE_INFO['data'] = page.get_paginated_data(serializers.data)

        return custom_response(ARTICLE_INFO, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[AllowAny | IsAuthenticated],
            authentication_classes=[CustomAuth])
    def get_article_info(self, request):
        """
        查看一篇文章
        :param request:
        :return:
        """
        try:
            article_id = int(request.query_params['id'])
            serializer = SimpleArticleSerializer(
                instance=SimpleArticleSerializer.get_instance().get(
                    id=article_id, publish_status=False))
        except (KeyError, ValueError, AttributeError, Article.DoesNotExist):
            return custom_response(PARAM_ERROR, 200)
        else:
            ARTICLE_INFO['data'] = serializer.data

        return custom_response(ARTICLE_INFO, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[AllowAny | IsAuthenticated],
            authentication_classes=[CustomAuth])
    def query_article(self, request):
        page = self.paginator
        try:
            filter_objects = query_combination(request.data)
            instances = SimpleArticleUserSerializer.get_instance().filter(
                filter_objects
            ).order_by(
                '-datetime_created'
            ).all()
        except (QueryException, ValueError):
            return custom_response(PARAM_ERROR, 200)
        else:
            page_list = page.paginate_queryset(instances, request, view=self)
            serializers = SimpleArticleUserSerializer(
                instance=page_list,
                many=True
            )
            ARTICLE_INFO['data'] = page.get_paginated_data(serializers.data)

        return custom_response(ARTICLE_INFO, 200)


class CommentViewSets(GenericViewSet):
    queryset = Comment.objects.all()
    authentication_classes = [CustomAuth]
    permission_classes = [IsAuthenticated | AllowAny]
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
        else:
            page = self.paginator
            instances = self.serializer_class.get_instance().filter(
                article_id=article_id
            ).all()
            page_list = page.paginate_queryset(instances, request, view=self)
            serializers = self.serializer_class(
                instance=page_list,
                many=True
            )

            COMMENT_INFO['data'] = page.get_paginated_data(serializers.data)

        return custom_response(COMMENT_INFO, 200)

    def create(self, request):
        """
        发表评论
        :param request:
        :return:
        """
        if request.user.is_anonymous:
            return custom_response(MUST_LOG_IN, 200)
        else:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)

        return custom_response(SUCCESS, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[IsAuthenticated],
            authentication_classes=[CustomAuth])
    def reply(self, request):
        """
        回复评论
        :param request:
        :return:
        """
        if request.user.is_anonymous:
            return custom_response(MUST_LOG_IN, 200)
        else:
            serializer = ReplySerializers(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)

        return custom_response(SUCCESS, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[IsAuthenticated],
            authentication_classes=[CustomAuth])
    def delete_comment(self, request):
        """
        删除评论
        :param request:
        :return:
        """
        try:
            comment_id = int(request.data['id'])
        except (KeyError, ValueError, AttributeError):
            return custom_response(PARAM_ERROR, 200)
        else:
            self.queryset.filter(
                id=comment_id,
                user=request.user
            ).delete()

        return custom_response(SUCCESS, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[IsAuthenticated],
            authentication_classes=[CustomAuth])
    def delete_reply(self, request):
        """
        删除回复
        :param request:
        :return:
        """
        try:
            reply_id = int(request.data['id'])
        except (KeyError, ValueError, AttributeError):
            return custom_response(PARAM_ERROR, 200)
        else:
            Reply.objects.filter(
                id=reply_id,
                user=request.user
            ).delete()

        return custom_response(SUCCESS, 200)
