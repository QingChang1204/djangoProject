LIMIT_LOG_EXPIRE_TIME = 30 * 60
LIMIT_LOG_MAX_TIME = 100
LOG_IN_URL_PATH = ('/api/user/log_in/', '/api/user/sign_up/')

REDIS_KEY = {
    "limit_key": 'limit_{}_{}'
}
