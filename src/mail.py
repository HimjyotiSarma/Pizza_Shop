from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from src.auth.utils import template_folder
from src.config import settings
from pydantic import EmailStr
from typing import List

message_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=template_folder,
)

mail = FastMail(config=message_config)


def create_message(recepients: List[EmailStr], subject: str, body: str):
    message = MessageSchema(
        recipients=recepients, subject=subject, body=body, subtype=MessageType.html
    )
    return message
