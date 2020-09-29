import json
import logging
import random
import uuid
import datetime
from collections import OrderedDict
from django.shortcuts import render
from elasticsearch_dsl import Search, Document, Text, Boolean, Date, Keyword, UpdateByQuery
from elasticsearch_dsl.connections import connections
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django_redis.pool import ConnectionFactory
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.pagination import PageNumberPagination
from aliyunsdkcore.request import RpcRequest
from aliyunsdkcore.client import AcsClient
from rest_framework.views import exception_handler
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from blog.errcode import AUTH_FAIL, NO_PERMISSION, NO_METHOD, UNKNOWN_ERROR
from blog.models import VerifyCode, User
from blog.constants import ARTICLE_INDEX

logger = logging.getLogger(__name__)


class DecodeConnectionFactory(ConnectionFactory):

    def get_connection(self, params):
        params['decode_responses'] = True
        return super().get_connection(params)


def custom_response(data, status, *args, **kwargs):
    return HttpResponse(json.dumps(data, ensure_ascii=False), status=status, *args, **kwargs)


class PaginationMixin:
    def get_paginated_data(self, data):
        return OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ])


def custom_exception_handler(exception, context):
    response = exception_handler(exception, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data['status_code'] = response.status_code

    if not settings.DEBUG:

        if response.data['status_code'] == 403:
            return custom_response(
                NO_PERMISSION, 200
            )
        elif response.data['status_code'] == 401:
            AUTH_FAIL['data'] = {
                'info': response.data.get('detail')
            }
            return custom_response(
                AUTH_FAIL, 200
            )
        elif response.data['status_code'] == 405:
            return custom_response(
                NO_METHOD, 200
            )
        elif response.data['status_code'] == 404:
            return render(None, '404.html', status=response.data['status_code'])
        elif 405 < response.data['status_code'] < 500:
            return custom_response(
                UNKNOWN_ERROR, response.data['status_code']
            )
    return response


class TenPagination(PageNumberPagination, PaginationMixin):
    page_size = 10


class TwentyPagination(PageNumberPagination, PaginationMixin):
    page_size = 20


class CustomAuth(JWTAuthentication):

    def get_user(self, validated_token):
        try:
            user_id = validated_token['user_id']
        except KeyError:
            raise InvalidToken('Token contained no recognizable user identification')

        user = User.objects.filter(**{'id': user_id}).only(
            'is_active', 'is_staff', 'is_superuser', 'id'
        ).first()

        if not user.is_active:
            raise AuthenticationFailed('User is inactive', code='user_inactive')

        return user


class SendSMS:
    REGION = "cn-hangzhou"
    PRODUCT_NAME = "Dysmsapi"
    DOMAIN = "dysmsapi.aliyuncs.com"

    def __init__(self):
        self.acs_client = AcsClient(settings.ALIYUN_SMS_ACCESS_ID, settings.ALIYUN_SMS_ACCESS_KEY, self.REGION)

    def send_sms(self, template_param=None, **kwargs):
        sms_request = RpcRequest(self.PRODUCT_NAME, '2017-05-25', 'SendSms')

        sms_request.__params = {}
        sms_request.__params.update(**kwargs)

        if template_param is not None:
            sms_request.__params.update({'TemplateParam': template_param})
        sms_request.set_query_params(sms_request.__params)

        sms_response = self.acs_client.do_action_with_exception(sms_request)

        return sms_response

    def send_code_message(self, phone):
        code = ''.join(str(random.choice(range(10))) for _ in range(6))
        __business_id = uuid.uuid1()
        params = '{"code":"' + code + '"}'
        response = self.send_sms(template_param=params,
                                 OutId=__business_id,
                                 PhoneNumbers=str(phone),
                                 SignName=settings.SMS_SIGN_NAME,
                                 TemplateCode=settings.SMS_TEMPLATE_CODE,
                                 )
        return_code = json.loads(response.decode('utf-8')).get('Code', 0)
        if return_code == 'OK':
            code_info, create_status = VerifyCode.objects.get_or_create(
                phone=phone,
            )
            code_info.code = code
            code_info.sent = timezone.now()
            code_info.save(update_fields=['code', 'sent'])
            return True, return_code
        else:
            return False, return_code

    def send_warning_message(self, phone):
        __business_id = uuid.uuid1()
        response = self.send_sms(OutId=__business_id,
                                 SignName=settings.SMS_SIGN_NAME,
                                 PhoneNumbers=phone,
                                 TemplateCode=settings.SMS_TEMPLATE_CODE,
                                 )

        return_code = json.loads(response.decode('utf-8')).get('Code', 0)
        if return_code == 'OK':
            return True, return_code
        else:
            return False, return_code


send_sms = SendSMS()

connections.create_connection(
    hosts=[settings.ES_URL],
    http_auth=(settings.ES_USER, settings.ES_PASSWORD),
    port=9200,
    use_ssl=False
)
article_index = ARTICLE_INDEX


class Article(Document):
    search_word = Text(analyzer="ik_max_word")
    author = Text(fields={'raw': Keyword()})
    datetime_created = Date()
    publish_status = Boolean()

    class Index:
        name = article_index

    def save(self, **kwargs):
        self.datetime_created = datetime.datetime.now()
        return super().save(**kwargs)


class SearchByEs:

    def __init__(self):
        Article.init()
        self.article = Article

    def handle_search(self, article_id, search_word, publish_status, author):
        article = self.article(
            meta={'id': article_id},
            author=author,
            search_word=search_word,
            publish_status=publish_status,
        )
        article.save()

    @staticmethod
    def update_search_by_author(old_author, new_author):
        ubq = UpdateByQuery(index=article_index).query(
            "match_phrase", author=old_author
        ).script(
            source="ctx._source.author = params.author",
            lang='painless',
            params={
                'author': new_author
            }
        )
        ubq.execute()

    @staticmethod
    def query_search(search_word, page=1, page_size=10):
        search = Search(
            index=article_index
        ).query(
            "multi_match", query=search_word, fields=['author', 'search_word']
        ).query(
            "match_phrase", publish_status=True
        ).sort(
            '-datetime_created'
        ).source(
            '_id'
        )[(page - 1) * page_size: page * page_size]
        res_count = search.count()
        res = search.execute()

        return res.to_dict(), res_count

    def delete_search(self, article_id):
        search = self.article.get(id=article_id, ignore=404)
        if search is not None:
            search.delete()


es_search = SearchByEs()
