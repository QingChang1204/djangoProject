import json
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django_redis import get_redis_connection
from blog.constants import LIMIT_LOG_MAX_TIME, LIMIT_LOG_EXPIRE_TIME, LOG_IN_URL_PATH, REDIS_KEY
from .utils import logger


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class RequestLimit:
    def __init__(self):
        self.redis = get_redis_connection()

    def check(self, code, user_id, increment):
        key = REDIS_KEY['limit_key'].format(code, user_id)
        timers = self.redis.get(key)
        logger.info('当前的时间次数是：{}'.format(timers))
        timers = int(timers) if timers else 0
        if timers:
            if timers <= LIMIT_LOG_MAX_TIME:
                timers = self.redis.incrby(key, increment)
                if timers == 1:
                    self.redis.expire(key, LIMIT_LOG_EXPIRE_TIME)
        else:
            self.redis.set(key, 1, LIMIT_LOG_EXPIRE_TIME)

        success = timers <= LIMIT_LOG_MAX_TIME
        if not success:
            logger.info('校验失败, code: {}, key: {}'.format(code, user_id))
        return success


def check_prevent(user_id, ip, increment):
    prevent_client = RequestLimit()
    if user_id is not None:
        success = prevent_client.check('user_limit', user_id, increment)
    else:
        success = prevent_client.check('user_limit', ip, increment)
    return success


class PreventMiddleware(MiddlewareMixin):
    @staticmethod
    def process_request(request):
        data = {}
        path = request.path
        if path in LOG_IN_URL_PATH:
            if request.user.is_anonymous:
                user_id = None
            else:
                user_id = request.user.id
            ip = get_client_ip(request)
            increment = 1
            write_success = check_prevent(user_id, ip, increment)

            if not write_success:
                data["msg"] = "您的访问过于频繁，请稍后再试"
                return HttpResponse(json.dumps(data, ensure_ascii=False), status=400)
