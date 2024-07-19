import email
import imaplib
import json
import asyncio
import html2text
from datetime import datetime
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from email.header import decode_header
from channels.generic.websocket import AsyncWebsocketConsumer
from email_messages.models import Message, MailAccount, MessageFile


class WebSocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        email_service = data["emailService"]
        login = data["login"]
        password = data["password"]

        account, created = await MailAccount.objects.aget_or_create(
            login=login,
            password=password,
            email_service=email_service
        )

        connection = imaplib.IMAP4_SSL(f'imap.{email_service}')
        connection.login(login, password)

        # Выбор входящих
        connection.select('INBOX')

        # Поиск последнего загруженного письма и получение списка неполученных писем
        last_message = await Message.objects.\
            filter(account__email_service=email_service).\
            order_by('-mail_index').afirst()
        last_message_index = 1 if last_message is None else last_message.mail_index + 1

        result, data = connection.uid('search', f'UID {last_message_index}:*')
        total_messages = len(data[0].split())

        await self.send(text_data=json.dumps({'total_messages': total_messages}))
        await asyncio.sleep(0.1)
        remaining_messages = total_messages

        for num in data[0].split():
            mail_index = num.decode()
            result, message_data = connection.uid('fetch', num, '(RFC822)')
            raw_email = message_data[0][1]

            # Получение email
            email_message = email.message_from_bytes(raw_email)

            # Получение заголовка
            subject = self.get_email_subject(email_message)

            # Получение даты отправки и получения
            date_dispatch, date_receipt = self.get_email_dates(email_message)

            # Получение содержимого
            message_content = self.get_email_content(email_message)

            # Получение вложений
            attachments = self.get_email_attachments(email_message)

            # Создание сообщения в базе данных
            message = await Message.objects.acreate(
                title=subject,
                date_dispatch=date_dispatch,
                date_receipt=date_receipt,
                text=message_content,
                account=account,
                mail_index=mail_index,
            )

            for filename, attachment in attachments:
                temp_file = NamedTemporaryFile()
                if attachment is None:
                    continue
                temp_file.write(attachment)
                temp_file.flush()
                await MessageFile.objects.acreate(message=message, file=File(temp_file, name=filename))

            remaining_messages -= 1
            await self.send(text_data=json.dumps({'remaining_messages': remaining_messages}))
            await asyncio.sleep(0.1)

            # Отправка сообщения на фронтенд
            await self.send(text_data=json.dumps({
                'emails': [
                    {
                        'title': subject,
                        'text': message_content,
                        'received_at': date_receipt,
                        'email_service': f'{login}@{email_service}',
                    }
                ]
            }))
            await asyncio.sleep(0.2)

        connection.close()
        connection.logout()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("import", self.channel_name)

    def get_email_subject(self, email_message):
        if 'Subject' in email_message and email_message['Subject'] is not None:
            subject, encoding = decode_header(email_message['Subject'])[0]
            if isinstance(subject, bytes) and encoding is not None:
                try:
                    subject = subject.decode(encoding)
                except LookupError:
                    subject = subject.decode('windows-1251')
            elif isinstance(subject, bytes):
                subject = subject.decode('utf-8')
        else:
            subject = "No subject"
        return subject

    def get_email_dates(self, email_message):

        date_receipt_temp = email_message['Received'].split(',')[-1].strip().split(' ')
        date_receipt = f'{date_receipt_temp[0]} {date_receipt_temp[1]} {date_receipt_temp[2]}'

        if 'Date' in email_message and email_message['Date'] is not None:
            date_dispatch_temp = email_message['Date'].split(',')[-1].strip().split(' ')
            date_dispatch = f'{date_dispatch_temp[0]} {date_dispatch_temp[1]} {date_dispatch_temp[2]}'
        else:
            date_dispatch = date_receipt

        date_dispatch = datetime.strptime(date_dispatch, '%d %b %Y')
        date_receipt = datetime.strptime(date_receipt, '%d %b %Y')

        date_dispatch = date_dispatch.strftime('%Y-%m-%d')
        date_receipt = date_receipt.strftime('%Y-%m-%d')

        return date_dispatch, date_receipt

    def get_email_content(self, email_message):
        message_content = ''
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                body = part.get_payload(decode=True)
                charset = part.get_content_charset()

                if content_type == 'text/plain':
                    if charset is None:
                        try:
                            message_content = body.decode('windows-1251')
                        except UnicodeDecodeError:
                            message_content = body.decode('koi8-r', errors='ignore')
                    else:
                        message_content = body.decode(charset)
                    break
                elif content_type == 'text/html':
                    text_maker = html2text.HTML2Text()
                    text_maker.ignore_links = True
                    if charset is None:
                        try:
                            message_content = text_maker.handle(body.decode('windows-1251'))
                        except UnicodeDecodeError:
                            message_content = text_maker.handle(body.decode('koi8-r', errors='ignore'))
                    else:
                        message_content = text_maker.handle(body.decode(charset))
                    break
        else:
            content_type = email_message.get_content_type()
            body = email_message.get_payload(decode=True)
            charset = email_message.get_content_charset()

            if content_type == 'text/plain':
                if charset is None:
                    try:
                        message_content = body.decode('windows-1251')
                    except UnicodeDecodeError:
                        message_content = body.decode('koi8-r', errors='ignore')
                else:
                    message_content = body.decode(charset)
            elif content_type == 'text/html':
                text_maker = html2text.HTML2Text()
                text_maker.ignore_links = True
                if charset is None:
                    try:
                        message_content = text_maker.handle(body.decode('windows-1251'))
                    except UnicodeDecodeError:
                        message_content = text_maker.handle(body.decode('koi8-r', errors='ignore'))
                else:
                    message_content = text_maker.handle(body.decode(charset))
        return message_content

    def get_email_attachments(self, email_message):
        attachments = []

        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            if part.get('Content-Disposition') == 'inline':
                continue

            filename, encode = decode_header(part.get_filename())[0]

            if isinstance(filename, bytes) and encode:
                filename = filename.decode(encode)
            elif isinstance(filename, bytes):
                filename = filename.decode('windows-1251')

            if bool(filename):
                attachment = part.get_payload(decode=True)
                attachments.append((filename, attachment))
        return attachments