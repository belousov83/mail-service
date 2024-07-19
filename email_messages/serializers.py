from django.utils import dateformat
from rest_framework import serializers
from email_messages.models import Message, MailAccount, MessageFile


class MessageFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageFile
        fields = ('id', 'file')


class MessageSerializer(serializers.ModelSerializer):

    date_out = serializers.SerializerMethodField()
    date_in = serializers.SerializerMethodField()
    mail_account = serializers.SerializerMethodField()
    files = MessageFileSerializer(many=True, allow_null=True)

    class Meta:
        model = Message
        fields = ('id', 'mail_account', 'title', 'date_out', 'date_in', 'text', 'files')

    def get_mail_account(self, obj):
        return f'{obj.account.login}@{obj.account.email_service}'

    def get_date_in(self, obj):
        return dateformat.format(obj.date_receipt,'d E Y')

    def get_date_out(self, obj):
        return dateformat.format(obj.date_dispatch,'d E Y')

    def create(self, validated_data):
        return Message.objects.create(**validated_data)


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailAccount
        fields = "__all__"