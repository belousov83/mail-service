from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path(r'ws/import/', consumers.WebSocketConsumer.as_asgi()),
]