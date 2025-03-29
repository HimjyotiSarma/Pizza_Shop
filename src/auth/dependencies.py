from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException, status, Depends, Request, UploadFile, File
from typing import Optional, Dict
import cloudinary
import cloudinary.uploader
import os
import shutil
import tempfile
from src.auth.utils import decode_token
from src.db.redis import token_in_blacklist
from src.db.main import get_session
from src.db.models import User
from sqlmodel.ext.asyncio.session import AsyncSession
from src.auth.service import AuthService
from src.db.Types import User_Roles
from src.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_SECRET,
    secure=True,
)
# print("CLOUD NAME: ", settings.CLOUDINARY_NAME)


auth_service = AuthService()


class TokenBearer(HTTPBearer):
    def __init__(self, autoError: bool = True):
        super().__init__(auto_error=autoError)

    async def __call__(self, request: Request) -> Optional[Dict]:
        auth_token: HTTPAuthorizationCredentials = await super().__call__(request)

        token_data = decode_token(auth_token.credentials)
        print("Decoded Token Data:", token_data)

        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Token Data is Invalid or Expired",
                    "resolution": "Please get a new Token",
                },
            )

        jti_redis_info = await token_in_blacklist(token_data.get("jti"))
        if jti_redis_info:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Token is Blacklisted",
                    "resolution": "Please get a new Token",
                },
            )

        return self.verify_token_data(token_data)

    def verify_token_data(self, token_data: dict):
        # This is for Demonstation puspose only and This will run if there is an Implemantation Error
        raise NotImplemented("Please Override 'verify_token_data' in child class")


class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data):
        if token_data and not token_data.get("refresh"):
            return token_data
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please provide an Access Token",
        )


class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data):
        if token_data and token_data.get("refresh"):
            return token_data
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please provide a Refresh Token",
        )


async def get_current_user(
    token_details: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    user_email = token_details["user"]["email"]
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token data Invalid or Expired. Please Login and Try again",
        )
    user_details = await auth_service.get_user(user_email, session)
    if not user_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User details not found in the database",
        )
    return user_details


async def get_current_customer(
    token_details: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    user_id = token_details["user"]["user_id"]
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token data Invalid or Expired. Please Login and Try again",
        )
    customer_details = await auth_service.get_customer(user_id=user_id, session=session)
    if not customer_details.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User isn't verified yet. Please verify your account and try again",
        )
    if not customer_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer details not found in the database",
        )
    return customer_details


def save_temp_image(image_file: UploadFile = File(...)) -> str:
    allowed_types = {"image/jpeg", "image/png", "image/gif"}
    if image_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and GIF images are allowed",
        )
    temp_dir = tempfile.gettempdir()
    temp_path = f"{temp_dir}/{image_file.filename}"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(image_file.file, buffer)

    return temp_path


async def uploadCloudinary(localPath: str):
    try:
        if not localPath:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The Local Path of the file is unavailable.",
            )

        if not os.path.exists(localPath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Temporary file path is not available or incorrect.",
            )

        cloudinary_result = cloudinary.uploader.upload(
            localPath,
        )

        if os.path.exists(localPath):
            os.remove(localPath)

        return cloudinary_result

    except Exception as e:
        # ✅ Ensure file is deleted only if it exists
        if os.path.exists(localPath):
            os.remove(localPath)

        # ✅ Log or handle the error properly
        print(f"Error uploading to Cloudinary: {e}")

        return None


class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ):
        if user.role == User_Roles.CUSTOMER:
            customer_details = await auth_service.get_customer(
                user_id=user.uid, session=session
            )
            if not customer_details.is_verified:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Customer not verified. Please verify your account and try again",
                )

        if user.role in self.allowed_roles:
            return True
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You don't have permission to access this route",
        )
