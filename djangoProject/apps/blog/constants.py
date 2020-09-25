LOG_IN_URL_PATH = ('/api/user/log_in/', '/api/user/sign_up/')
COMMENT_URL_PATH = ('/api/comment/',)

LIMIT_INFO = {
    "log_in_limit": (30 * 60, 100),
    "comment_limit": (10 * 60, 1)
}
REDIS_KEY = {
    "limit_key": 'limit_{}_{}'
}
