import json
import logging
from django.http import HttpResponse
from django_redis.pool import ConnectionFactory
from blog.search import SearchByEs
logger = logging.getLogger(__name__)
search = SearchByEs()


class DecodeConnectionFactory(ConnectionFactory):

    def get_connection(self, params):
        params['decode_responses'] = True
        return super().get_connection(params)


def custom_response(data, status, *args, **kwargs):
    return HttpResponse(json.dumps(data, ensure_ascii=False), status=status, *args, **kwargs)
