import json
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django_redis import get_redis_connection
from blog.constants import LIMIT_LOG_MAX_TIME, LIMIT_LOG_EXPIRE_TIME, LOG_IN_URL_PATH, REDIS_KEY
from .utils import logger


class RequestLimit:
    def __init__(self):
        self.redis = get_redis_connection()

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def check(self, code, info):
        key = REDIS_KEY['limit_key'].format(code, info)
        timers = self.redis.get(key)
        timers = int(timers) if timers else 0
        logger.info('当前的时间次数是：{}'.format(timers))
        if timers:
            if timers <= LIMIT_LOG_MAX_TIME:
                timers = self.redis.incrby(key, 1)
                if timers == 1:
                    self.redis.expire(key, LIMIT_LOG_EXPIRE_TIME)
        else:
            self.redis.set(key, 1, LIMIT_LOG_EXPIRE_TIME)

        success = timers <= LIMIT_LOG_MAX_TIME
        if not success:
            logger.info('校验失败, code: {}, key: {}'.format(code, info))
        return success


prevent_client = RequestLimit()


class PreventMiddleware(MiddlewareMixin):
    @staticmethod
    def check_prevent(user_id, ip):
        if user_id is not None:
            success = prevent_client.check('user_limit', user_id)
        else:
            success = prevent_client.check('user_limit', ip)
        return success

    def process_request(self, request):
        data = {}
        path = request.path
        if path in LOG_IN_URL_PATH:
            if request.user.is_anonymous:
                user_id = None
            else:
                user_id = request.user.id
            ip = prevent_client.get_client_ip(request)
            request_success = self.check_prevent(user_id, ip)

            if not request_success:
                data["msg"] = "您的访问过于频繁，请稍后再试"
                return HttpResponse(json.dumps(data, ensure_ascii=False), status=400)
