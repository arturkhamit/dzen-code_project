from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .services.notifications import COMMENTS_GROUP


class CommentsConsumer(AsyncJsonWebsocketConsumer):
    # Public notifications contain no account data. Writes still use HTTP,
    # including its authentication, CSRF checks, validation, and CAPTCHA.
    async def connect(self):
        await self.channel_layer.group_add(COMMENTS_GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(COMMENTS_GROUP, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Keep long-lived tabs subscribed even after Redis group expiry/restarts.
        if content == {"type": "ping"}:
            await self.channel_layer.group_add(COMMENTS_GROUP, self.channel_name)
            await self.send_json({"type": "pong"})

    async def comments_changed(self, event):
        await self.send_json({"type": "comments.changed"})
