from urllib.parse import parse_qs
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from django.urls import path
from django.conf import settings
from django.contrib.auth import get_user_model
from channels.routing import ProtocolTypeRouter, URLRouter
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode

from blog.consumers import NotificationConsumer


def get_user(user_id):
    user = get_user_model().objects.filter(
        id=user_id
    ).only('id').first()
    return user if user is not None else AnonymousUser()


@database_sync_to_async
def get_user_from_scope(scope):
    try:
        token = parse_qs(scope["query_string"].decode("utf8"))["token"][0]
        UntypedToken(token)
    except (InvalidToken, TokenError, KeyError, TypeError):
        user = AnonymousUser()
    else:
        decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user = get_user(decoded_data["user_id"])
    return user


class JWTAuthMiddleWare:

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return JWTAuthMiddleWareInstance(scope, self)


class JWTAuthMiddleWareInstance:
    def __init__(self, scope, middleware):
        self.middleware = middleware
        self.scope = scope
        self.inner = self.middleware.inner

    async def __call__(self, receive, send):
        close_old_connections()
        self.scope['user'] = await get_user_from_scope(self.scope)
        inner = self.inner(self.scope)
        return await inner(receive, send)


JWTAuthStack = lambda inner: JWTAuthMiddleWare(
    AuthMiddlewareStack(inner)
)

websockets = URLRouter([
    path(
        "ws/notifications/",
        NotificationConsumer,
        name="ws_notifications",
    )
])

application = ProtocolTypeRouter({
    "websocket": JWTAuthStack(
        websockets
    )
})
