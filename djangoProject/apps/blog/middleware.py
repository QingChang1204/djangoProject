from django.utils.deprecation import MiddlewareMixin
from django_redis import get_redis_connection
from blog.constants import LIMIT_LOG_MAX_TIME, LIMIT_LOG_EXPIRE_TIME, LOG_IN_URL_PATH, REDIS_KEY
from blog.utils import logger, custom_response


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

    def check(self, check_type, info):
        key = REDIS_KEY['limit_key'].format(check_type, info)
        request_sum = self.redis.get(key)
        request_sum = int(request_sum) if request_sum else 0
        if request_sum:
            if request_sum <= LIMIT_LOG_MAX_TIME:
                request_sum = self.redis.incrby(key, 1)
                if request_sum == 1:
                    self.redis.expire(key, LIMIT_LOG_EXPIRE_TIME)
        else:
            self.redis.set(key, 1, LIMIT_LOG_EXPIRE_TIME)
        if not request_sum <= LIMIT_LOG_MAX_TIME:
            logger.info('请求次数超过限制, 校验类型: {}, Redis Key: {}'.format(check_type, info))
        return True


prevent_client = RequestLimit()


class PreventMiddleware(MiddlewareMixin):
    @staticmethod
    def check_prevent(user_id, ip, check_type):
        if user_id is not None:
            success = prevent_client.check(check_type, user_id)
        else:
            success = prevent_client.check(check_type, ip)
        return success

    def process_request(self, request):
        path = request.path
        if path in LOG_IN_URL_PATH:
            if request.user.is_anonymous:
                user_id = None
            else:
                user_id = request.user.id
            ip = prevent_client.get_client_ip(request)
            request_success = self.check_prevent(user_id, ip, "log_in_limit")
            if not request_success:
                return custom_response({"detail": "您的访问过于频繁，请稍后再试。"}, 401)
