import logging
from django_redis.pool import ConnectionFactory
from blog.search import SearchByEs

logger = logging.getLogger(__name__)
search = SearchByEs()


class DecodeConnectionFactory(ConnectionFactory):

    def get_connection(self, params):
        params['decode_responses'] = True
        return super().get_connection(params)
