import json

from channels.generic.websocket import AsyncWebsocketConsumer


class OrderNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "order_notifications"

        # Join group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Receive message from group
    async def order_placed(self, event):
        order_data = event["order"]

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps({"type": "order.placed", "order": order_data})
        )

    async def order_status_updated(self, event):
        order_data = event["order"]

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps({"type": "order.status_updated", "order": order_data})
        )


class RiderNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.group_name = f"rider_notifications_user_{user_id}"

        # Join group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Receive message from group
    async def order_rider_assigned(self, event):
        order_data = event["order"]

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps({"type": "order.rider_assigned", "order": order_data})
        )

    async def order_status_updated(self, event):
        order_data = event["order"]

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps({"type": "order.status_updated", "order": order_data})
        )
