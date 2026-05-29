import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import project_manager.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_manager.settings')

_django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': _django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(project_manager.routing.urlpatterns)
    ),
})

