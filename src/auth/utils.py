from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from pathlib import Path
import uuid
import jwt
import logging
from src.config import settings

from decimal import Decimal


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_password_hash(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_token(user_data: dict, isRefreshToken: bool = False):
    expiry_date = datetime.now() + (
        timedelta(minutes=10080) if isRefreshToken else timedelta(minutes=1440)
    )
    payload = {
        "jti": str(uuid.uuid4()),
        "user": user_data,
        "expiry": expiry_date.isoformat(),
        "refresh": isRefreshToken,
    }
    token_id = jwt.encode(
        payload=payload, key=settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return token_id


def decode_token(jwt_token: str):
    try:
        token_data = jwt.decode(
            jwt=jwt_token, key=settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return token_data
    except jwt.PyJWKError as jwte:
        logging.exception(jwte)
        return None
    except Exception as e:
        logging.exception(e)
        return None


def create_safe_token(data: dict):
    try:
        serializer = URLSafeTimedSerializer(secret_key=settings.DANGEROUS_TOKEN)
        token = serializer.dumps(data, salt="email verification")
        return token
    except Exception as e:
        logging.error(f"Error Creating Dangerous Token : {str(e)}")
        return None


def decode_safe_token(token: str):
    try:
        serializer = URLSafeTimedSerializer(secret_key=settings.DANGEROUS_TOKEN)
        token_data = serializer.loads(
            token, max_age=settings.DANGEROUS_MAX_AGE, salt="email verification"
        )
        return token_data
    except SignatureExpired as e:
        logging.error(f"Safe Token Expired: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error Decoding Safe Token : {str(e)}")


# Convert dict values to string


def convert_str(obj: dict):
    return {
        key: str(value) if isinstance(value, (uuid.UUID, datetime, Decimal)) else value
        for key, value in obj.items()
    }


BASE_DIR = Path(__file__).resolve().parent.parent
template_folder = Path(BASE_DIR, "templates")
templates = Jinja2Templates(directory=f"{template_folder}")
