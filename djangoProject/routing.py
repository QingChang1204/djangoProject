from urllib.parse import parse_qs
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from django.urls import path
from django.contrib.auth import get_user_model
from channels.routing import ProtocolTypeRouter, URLRouter

from blog.consumers import NotificationConsumer
from blog.models import WebSocketTicket


@database_sync_to_async
def get_user_from_scope(scope):
    try:
        token = parse_qs(scope["query_string"].decode("utf8"))["token"][0]
        ticket = WebSocketTicket.objects.select_related(
            'user'
        ).only('user_id', 'user__username', 'id').get(ticket=token)
        user = ticket.user
        ticket.delete()
    except (KeyError, TypeError, WebSocketTicket.DoesNotExist):
        user = AnonymousUser()

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
