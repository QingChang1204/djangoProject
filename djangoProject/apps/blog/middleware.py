from django.utils.deprecation import MiddlewareMixin
from django_redis import get_redis_connection
from blog.constants import LOG_IN_URL_PATH, REDIS_KEY, COMMENT_URL_PATH, \
    LIMIT_INFO
from blog.utils import logger, custom_response


class RequestLimit:
    def __init__(self):
        self.redis = get_redis_connection()

    @staticmethod
    def get_client_ip(request):
        """
        获得ip地址
        :param request:
        :return:
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def check(self, check_type, info):
        """
        检查请求次数
        :param check_type:
        :param info:
        :return:
        """
        key = REDIS_KEY['limit_key'].format(check_type, info)
        request_sum = self.redis.get(key)
        request_sum = int(request_sum) if request_sum else 0
        limit_expired_time, limit_max = LIMIT_INFO.get(check_type, (5 * 60, 100))
        if request_sum:
            if request_sum <= limit_max:
                request_sum = self.redis.incrby(key, 1)
                if request_sum == 1:
                    self.redis.expire(key, limit_expired_time)
        else:
            self.redis.set(key, 1, limit_expired_time)
        if not request_sum <= limit_max:
            logger.info('请求次数超过限制, 校验类型: {}, Redis Key: {}'.format(check_type, info))
            return False
        return True


prevent_client = RequestLimit()


class PreventMiddleware(MiddlewareMixin):
    @staticmethod
    def check_prevent(user_id, ip, check_type):
        """
        检查请求次数
        :param user_id:
        :param ip:
        :param check_type:
        :return:
        """
        if user_id is not None:
            success = prevent_client.check(check_type, user_id)
        else:
            success = prevent_client.check(check_type, ip)
        return success

    def process_request(self, request):
        path = request.path
        if request.method in ['PUT', 'POST']:
            try:
                if request.user.is_anonymous:
                    user_id = None
                else:
                    user_id = request.user.id
            except AttributeError:
                user_id = None

            if path in LOG_IN_URL_PATH:
                ip = prevent_client.get_client_ip(request)
                request_success = self.check_prevent(user_id, ip, "log_in_limit")
                if not request_success:
                    return custom_response({"detail": "您的访问过于频繁，请稍后再试。"}, 401)
            elif path in COMMENT_URL_PATH:
                ip = prevent_client.get_client_ip(request)
                request_success = self.check_prevent(user_id, ip, "comment_limit")
                if not request_success:
                    return custom_response({"detail": "您的评论或回复过于频繁，请稍后再试。"}, 404)
