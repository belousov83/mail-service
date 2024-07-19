from django.urls import path, include
from rest_framework.routers import DefaultRouter
from email_messages.views import MessageViewSet, AccountViewSet, import_messages

router = DefaultRouter(trailing_slash=True)
router.register(r"email_messages", MessageViewSet)
router.register(r"accounts", AccountViewSet)

urlpatterns = [
    path(r"", include(router.urls)),
    path("import-messages/", import_messages, name="import_messages"),
]