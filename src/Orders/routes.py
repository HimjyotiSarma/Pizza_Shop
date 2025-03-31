from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from src.db.models import Customer
from src.auth.dependencies import (
    RoleChecker,
    get_current_customer,
)
from src.db.Types import OrderStatus
from src.auth.utils import convert_str
from .schemas import OrderSchema, Order_Items_Schema, UpdateOrderSchema
from .service import OrderService

all_user_checker = Depends(RoleChecker(["admin", "manager", "staff", "customer"]))
management_checker = Depends(RoleChecker(["admin", "manager", "staff"]))
customer_checker = Depends(RoleChecker(["customer"]))
admin_checker = Depends(RoleChecker(["admin"]))
manager_user = Depends(RoleChecker(["manager"]))
admin_manager_checker = Depends(RoleChecker(["admin", "manager"]))


order_router = APIRouter()
order_service = OrderService()


# TODO :-> Add Payments Services
# TODO :-> CREATE A CRON SCHEDULE TO CHECK EVERY 30 minutes THAT THE newly created Order has its respective Order-Item Tables or Not
# IF THERE IS ANY EMPTY ROW with order_id is null in Order_Items with its respective Orders table then Delete that Order
@order_router.get("/order_detail/{order_id}", dependencies=[all_user_checker])
async def get_order_details(
    order_id: str, session: AsyncSession = Depends(get_session)
):
    try:
        order_details = await order_service.get_order(
            order_id=order_id, session=session
        )
        return JSONResponse(
            content={
                "message": f"Order details fetched successfully",
                "orders": convert_str(order_details.model_dump()),
            },
            status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding Order details -> {str(e)}",
        )


# Create All Orders related to a Customer
@order_router.get("/all_orders/{order_status}")
async def get_all_orders(
    order_status: str = "all",
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_session),
):
    try:
        order_status = (
            OrderStatus(order_status) if order_status != "all" else order_status
        )
        all_orders = await order_service.get_all_customer_orders(
            customer_id=customer.uid, order_status=order_status, session=session
        )
        return JSONResponse(
            content={
                "message": f"Order details fetched successfully",
                "orders": all_orders,
            },
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting Orders -> {str(e)}",
        )


@order_router.get(
    "/get_uncompleted_orders/{time_range}", dependencies=[management_checker]
)
async def get_all_uncompleted_orders(
    time_range: int, session: AsyncSession = Depends(get_session)
):
    try:
        datetime_range = (
            (datetime.now(timezone.utc) - timedelta(minutes=time_range))
            if time_range
            else (datetime.now(timezone.utc) - timedelta(minutes=1440))
        )
        uncomplted_orders = await order_service.get_uncompleted_orders(
            time_range=datetime_range, session=session
        )
        return JSONResponse(
            content={
                "message": f"All Uncompleted Orders under time range {str(datetime_range)}",
                "orders": uncomplted_orders,
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting Uncompleted Orders -> {str(e)}",
        )


@order_router.post("/create_order")
async def create_new_order(
    order_info: OrderSchema,
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_session),
):
    try:
        new_order = await order_service.create_Order(
            customer_id=customer.uid, order_details=order_info, session=session
        )
        return JSONResponse(
            content={
                "message": "Order Successfully Created",
                "order": convert_str(new_order.model_dump()),
            },
            status_code=status.HTTP_201_CREATED,
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error Creating New Order -> {str(e)}",
        )


@order_router.post("/create_order_list", dependencies=[customer_checker])
async def create_order_lists(
    order_item_list: Order_Items_Schema,
    session: AsyncSession = Depends(get_session),
):
    try:
        new_order_list = await order_service.create_Items_Order_list(
            order_items_list=order_item_list, session=session
        )
        return JSONResponse(
            content={
                "message": "Items Added to Order Successfully",
                "order_items": new_order_list,
            },
            status_code=status.HTTP_200_OK,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error Creating Order List -> {str(e)}",
        )


@order_router.patch("/cancel_order/{order_id}")
async def cancel_customer_order(
    order_id: str,
    customer: Customer = Depends(get_current_customer),
    session: AsyncSession = Depends(get_session),
):
    try:
        order_details = await order_service.get_order(
            order_id=order_id, session=session
        )
        if order_details is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with id {str(order_id)} is not present in the database",
            )
        if order_details.customer_id != customer.uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cancelling other user's order is not allowed",
            )
        cancel_order_result = await order_service.cancel_orders(
            order=order_details, session=session
        )
        if cancel_order_result is True:
            return JSONResponse(
                content={
                    "message": "Order Cancelled successfully",
                },
                status_code=status.HTTP_200_OK,
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Something went wrong when cancelling Order",
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error Updating Order -> {str(e)}",
        )


@order_router.patch("/update/{order_id}", dependencies=[admin_manager_checker])
async def update_orders_for_customer(
    order_id: str,
    updated_order: UpdateOrderSchema,
    session: AsyncSession = Depends(get_session),
):
    try:
        order_details = await order_service.get_order(
            order_id=order_id, session=session
        )
        if order_details is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with id {str(order_id)} is not present in the database",
            )
        updated_order_result = await order_service.update_orders(
            order=order_details, updated_order_details=updated_order, session=session
        )
        return JSONResponse(
            content={
                "message": "Order Updated successfully",
                "order_details": convert_str(updated_order_result.model_dump()),
            },
            status_code=status.HTTP_200_OK,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error Updating Order -> {str(e)}",
        )
