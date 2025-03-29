from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from src.db.models import Customer
from src.auth.dependencies import (
    AccessTokenBearer,
    RefreshTokenBearer,
    RoleChecker,
    get_current_customer,
)
from src.auth.utils import convert_str
from .service import AddressService
from .schema import AddressSchema, UpdateAddressSchema

address_router = APIRouter()
address_service = AddressService()


@address_router.get("/all")
async def get_all_delivery_details(
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_session),
):
    try:
        all_delivery_address = await address_service.get_all_address(
            customer_id=str(customer.uid), session=session
        )
        return JSONResponse(
            content={
                "message": "All Addresses fetched successfully",
                "address_details": all_delivery_address,
            },
            status_code=status.HTTP_200_OK,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting address details -> {str(e)}",
        )


@address_router.post("/create")
async def create_new_address(
    address_details: AddressSchema,
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_session),
):
    try:
        new_address_details = await address_service.create_address(
            customer_id=str(customer.uid),
            address_details=address_details,
            session=session,
        )
        return JSONResponse(
            content={
                "message": "New Address Created successfully",
                "address": convert_str(new_address_details.model_dump()),
            },
            status_code=status.HTTP_201_CREATED,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error Creating New Address ->  {str(e)}",
        )


@address_router.patch("/update/{address_id}")
async def update_address_details(
    address_id: str,
    updated_address: UpdateAddressSchema,
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_session),
):
    try:
        delivery_address_info = await address_service.get_address(
            address_id=address_id, session=session
        )
        updated_delivery = await address_service.update_address(
            customer_id=str(customer.uid),
            address=delivery_address_info,
            updated_address=updated_address,
            session=session,
        )
        return JSONResponse(
            content={
                "message": "Address Updated successfully",
                "address": convert_str(updated_delivery.model_dump()),
            },
            status_code=status.HTTP_201_CREATED,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error Updating delivery Detail -> {str(e)}",
        )


@address_router.delete("/delete/{address_id}")
async def delete_delivery_details(
    address_id: str,
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_session),
):
    try:
        is_deleted = await address_service.delete_address(
            customer_id=str(customer.uid), address_id=address_id, session=session
        )
        if not is_deleted:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Address isn't deleted due to some unexpected reason",
            )
        return JSONResponse(
            content={
                "message": "Address deleted Succesfully",
                "deleted_address_id": address_id,
            },
            status_code=status.HTTP_202_ACCEPTED,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error Deleting Address: {str(e)}",
        )
