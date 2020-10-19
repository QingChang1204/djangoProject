import json

from channels.db import database_sync_to_async
from channels.exceptions import AcceptConnection, DenyConnection
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from blog.models import ReceiveMessage


@database_sync_to_async
def set_message(user_id, send_user_id, content):
    ReceiveMessage.objects.create(
        user_id=user_id,
        content=content,
        send_user_id=send_user_id
    )


class NotificationConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = "message_{}"
        self.channel_layer = get_channel_layer()

    async def websocket_connect(self, message):
        if self.scope.get("user", AnonymousUser()).is_anonymous:
            await self.close()
        try:
            await self.connect()
        except AcceptConnection:
            await self.accept()
        except DenyConnection:
            await self.close()

    async def connect(self):
        await self.channel_layer.group_add(
            self.group_name.format(
                self.scope['user'].id
            ), self.channel_name
        )
        await self.accept()

    async def disconnect(self, code):
        if self.scope.get("user", AnonymousUser()).is_anonymous:
            pass
        else:
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name
            )

    async def receive_json(self, content, **kwargs):
        await set_message(
            send_user_id=self.scope['user'].id,
            content=content['content'],
            user_id=content['user_id']
        )

    async def chat_message(self, event):
        close_old_connections()
        await self.send_json(
            {
                'content': event['message'],
                'send_user': event['send_user']
            }
        )

    @classmethod
    async def encode_json(cls, text_data):
        return json.dumps(text_data, ensure_ascii=False)
