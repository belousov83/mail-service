"""
ASGI config for dev project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dev.settings')
django.setup()

from . import routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(routing.websocket_urlpatterns),
})
