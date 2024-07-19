from django.db import models


class MailAccount(models.Model):
    login = models.CharField(max_length=20)
    password = models.CharField(max_length=20)
    email_service = models.CharField(max_length=20)


class Message(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name='Тема сообщения')
    date_dispatch = models.DateField(verbose_name='Дата отправки')
    date_receipt = models.DateField(verbose_name='Дата получения')
    text = models.TextField(blank=True, null=True, verbose_name='Текст сообщения')
    account = models.ForeignKey(MailAccount, related_name="messages_app", on_delete=models.CASCADE)
    mail_index = models.PositiveIntegerField(verbose_name='Уникальный индекс письма на почте')


class MessageFile(models.Model):
    message = models.ForeignKey(to='Message', related_name="files", on_delete=models.PROTECT, verbose_name="Сообщение")
    file = models.FileField(upload_to='files/')