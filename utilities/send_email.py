from config import settings
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from .database import get_db

class EmailSchema(BaseModel):
    email: EmailStr


conf = ConnectionConfig(
    MAIL_USERNAME="hassansabri172@gmail.com",
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM="hassansabri172@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="Demo APP",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

async def send_email(email: str,subject: str,message: str):
    email_message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=message,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(email_message)