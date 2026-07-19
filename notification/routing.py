from django.urls import path

from .consumers import OrderNotificationConsumer, RiderNotificationConsumer

websocket_urlpatterns = [
    path("ws/notifications/", OrderNotificationConsumer.as_asgi()),
    path("ws/rider/notifications/<int:user_id>/", RiderNotificationConsumer.as_asgi()),
    path("ws/vendor/notifications/<int:user_id>/", RiderNotificationConsumer.as_asgi()),
]
