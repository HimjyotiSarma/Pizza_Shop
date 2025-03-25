from fastapi import status, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, join
from pydantic import EmailStr
from sqlalchemy.orm import selectinload
import uuid

from src.db.models import Customer, User
from .schema import UserSchema, PasswordConfirmSchema, UserUpdateSchema, UserRoleUpdate
from src.auth.utils import generate_password_hash


class AuthService:
    async def get_user(self, email: EmailStr, session: AsyncSession):
        try:
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Please provide email and try again",
                )

            statement = select(User).where(User.email == email)
            result = await session.exec(statement)
            user = result.first()
            return user

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error getting User: {str(e)}",
            )

    async def get_user_by_uid(self, user_id: str, session: AsyncSession) -> User:
        try:
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Please provide user id and try again",
                )

            statement = select(User).where(User.uid == user_id)
            result = await session.exec(statement)
            user = result.one()
            return user

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error getting User: {str(e)}",
            )

    async def get_customer(self, user_id: str, session: AsyncSession):
        try:
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Please provide user id and try again",
                )

            statement = select(Customer).where(Customer.user_id == user_id)
            result = await session.exec(statement)
            customer = result.first()
            return customer

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error getting Customer Info : {str(e)}",
            )

    async def get_user_cum_customer(self, email: str, session: AsyncSession):
        try:
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Please provide email and try again",
                )

            statement = select(User, Customer).join(Customer).where(User.email == email)
            result = await session.exec(statement)
            user = result.first()
            return user

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error getting Customer Info : {str(e)}",
            )

    async def user_exist(self, email: EmailStr, session: AsyncSession) -> bool:
        user = await self.get_user(email, session)
        return user is not None

    async def create_user(self, user_details: UserSchema, session: AsyncSession):
        try:
            user_details_dict = user_details.model_dump()
            if "is_verified" in user_details_dict:
                raise HTTPException(
                    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                    detail=f"Manual Verification of Account isn't allowed",
                )
            password_val = user_details_dict.pop("password", None)
            new_user = User(**user_details_dict)
            if password_val:
                new_user.password_hash = generate_password_hash(password_val)
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error Creating New User: {str(e)}",
            )

    async def create_customer(self, user_email: EmailStr, session: AsyncSession):
        try:
            user_data = await self.get_user(user_email, session)
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User doesn't exist in the database.",
                )
            new_customer = Customer(user_id=user_data.uid, is_verified=False)
            session.add(new_customer)
            await session.commit()
            await session.refresh(new_customer)
            return new_customer
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error Creating New Customer: {str(e)}",
            )

    async def create_customer_with_user_id(
        self, user_id: uuid.uuid4, session: AsyncSession
    ):
        try:
            # user_data = await self.get_user(user_email, session)
            # if not user_data:
            #     raise HTTPException(
            #         status_code=status.HTTP_404_NOT_FOUND,
            #         detail=f"User doesn't exist in the database.",
            #     )
            new_customer = Customer(user_id=user_id, is_verified=False)
            session.add(new_customer)
            await session.commit()
            await session.refresh(new_customer)
            return new_customer
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error Creating New Customer: {str(e)}",
            )

    async def update_user(
        self, user: User, updated_schema: UserUpdateSchema, session: AsyncSession
    ):
        try:
            updated_info = updated_schema.model_dump()
            if "password" in updated_info or "password_hash" in updated_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Please use the update password api call for this operation",
                )
            if "role" in updated_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Please use the update role api for this operation",
                )
            user

            for key, value in updated_info.items():
                if hasattr(user, key):
                    setattr(user, key, value)
                else:
                    raise ValueError(f"Invalid Key Attribute : {key}")

            await session.commit()
            await session.refresh(user)

            return user

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error Updating User Info: {str(e)}",
            )

    async def update_user_role(
        self, user: User, updated_schema: UserRoleUpdate, session: AsyncSession
    ):
        updated_info = updated_schema.model_dump()

        new_role = updated_info.get("role")
        if not new_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role field is required.",
            )

        if user.role == new_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="New role and previous role are the same.",
            )

        # Update role
        user.role = new_role

        try:
            await session.commit()
            await session.refresh(user)
            return user
        except Exception as e:
            await session.rollback()  # Ensure rollback on failure
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user role: {str(e)}",
            )

    async def update_customer(
        self, customer: Customer, updated_info: dict, session: AsyncSession
    ):
        try:
            if "password" in updated_info or "password_hash" in updated_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Please use the update password api call for this operation",
                )

            for key, value in updated_info.items():
                if hasattr(customer, key):
                    setattr(customer, key, value)
                else:
                    raise ValueError(f"Invalid Key Attribute : {key}")

            await session.commit()
            await session.refresh(customer)

            return JSONResponse(
                content={
                    "message": f"Customer with user id {str(customer.user_id)} has been updated succesfully"
                }
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error Updating Customer Info: {str(e)}",
            )

    async def update_password(
        self,
        user: User,
        new_password_schema: PasswordConfirmSchema,
        session: AsyncSession,
    ):
        try:
            if new_password_schema.new_password != new_password_schema.confirm_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password and confirm password do not match.",
                )

            user.password_hash = generate_password_hash(
                new_password_schema.new_password
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
        except Exception as e:
            await session.rollback()  # Rollback in case of error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating password: {str(e)}",
            )
