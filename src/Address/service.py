from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.db.models import Delivery_Address, User
from src.auth.utils import convert_str
from fastapi import status, HTTPException
import uuid

from .schema import AddressSchema, UpdateAddressSchema


class AddressService:
    async def get_all_address(self, customer_id: str, session: AsyncSession):
        try:
            statement = select(Delivery_Address).where(
                Delivery_Address.customer_id == customer_id
            )
            result = await session.exec(statement)
            address_details = result.all()
            converted_addresses = [
                convert_str(address.model_dump()) for address in address_details
            ]
            return converted_addresses

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting Addresses for user -> {str(e)}",
            )

    async def get_address(self, address_id: str, session: AsyncSession):
        try:
            statement = select(Delivery_Address).where(
                Delivery_Address.uid == address_id
            )
            result = await session.exec(statement)
            address = result.first()
            if address is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Address with Id {str(address_id)} is unavailable in the database",
                )
            return address
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting address info: {str(e)}",
            )

    async def create_address(
        self, customer_id: str, address_details: AddressSchema, session: AsyncSession
    ):
        # The Customer Id is a URL parameter
        try:
            address_details_dict = address_details.model_dump(exclude_unset=True)
            address_details_dict["customer_id"] = customer_id
            print(address_details_dict)
            new_address = Delivery_Address(**address_details_dict)
            session.add(new_address)
            await session.commit()
            await session.refresh(new_address)
            return new_address
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error Creating New Address: {str(e)}",
            )

    async def update_address(
        self,
        customer_id: str,
        address: Delivery_Address,
        updated_address: UpdateAddressSchema,
        session: AsyncSession,
    ):
        # Ensure that Either The actual user with User's customer id should match the current User's customer id
        try:
            # address_info = await self.get_address(
            #     address_id=address_id, session=session
            # )
            if customer_id != str(address.customer_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Updating Address of other user is not allowed",
                )
            updated_address_dict = updated_address.model_dump(exclude_unset=True)
            print("UPDATED DETAILS:  ->  ", updated_address_dict)

            for key, value in updated_address_dict.items():
                if hasattr(address, key):
                    setattr(address, key, value)
                else:
                    raise ValueError(f"Invalid key attribute {str(key)}")
            await session.commit()
            await session.refresh(address)
            return address
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error Updating Address: {str(e)}",
            )

    async def delete_address(
        self, customer_id: str, address_id: str, session: AsyncSession
    ):
        try:
            delivery_details = await self.get_address(
                address_id=address_id, session=session
            )
            if customer_id != str(delivery_details.customer_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Deleting Address of other User is not permitted",
                )
            await session.delete(delivery_details)
            await session.commit()
            return True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error Deleting Delivery Address: {str(e)}",
            )
