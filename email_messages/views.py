from django.shortcuts import render
from rest_framework import viewsets, mixins
from email_messages.models import Message, MailAccount
from email_messages.serializers import MessageSerializer, AccountSerializer


class MessageViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer


class AccountViewSet(viewsets.ModelViewSet):
    queryset = MailAccount.objects.all()
    serializer_class = AccountSerializer


def import_messages(request):
    return render(request, 'email_messages/index.html')