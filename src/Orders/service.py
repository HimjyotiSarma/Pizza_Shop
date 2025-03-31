from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
from src.db.models import Order, Order_Items, User, Customer
from src.auth.utils import convert_str
from datetime import datetime
from typing import List
from .schemas import OrderSchema, Order_Items_Schema, Item_Quantity, UpdateOrderSchema
from src.items_Categories.service import ItemService
from src.db.Types import OrderStatus
import uuid

item_service = ItemService()


class OrderService:
    async def get_uncompleted_orders(self, time_range: datetime, session: AsyncSession):
        try:
            statement = (
                select(Order)
                .where(Order.created_at >= time_range)
                .where(Order.order_status != OrderStatus.CANCELLED)
                .where(Order.order_status != OrderStatus.DELIVERED)
            )
            result = (await session.exec(statement))._allrows()
            print("ALL UNCOMPLETED ORDERS ---> ", result)
            converted_result = [convert_str(order.model_dump()) for order in result]
            return converted_result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error Getting Uncompleted Orders -> {str(e)}",
            )

    async def get_all_customer_orders(
        self, customer_id: str, order_status: OrderStatus | str, session: AsyncSession
    ):
        try:
            if type(order_status) == str and order_status != "all":
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail=f"{str(order_status)} is not a valid Order status parameter",
                )
            statement = (
                select(Order).where(Order.customer_id == customer_id)
                if order_status == "all"
                else select(Order)
                .where(Order.customer_id == customer_id)
                .where(Order.order_status == order_status)
            )
            result = (await session.exec(statement))._allrows()
            converted_result = [convert_str(order.model_dump()) for order in result]
            return converted_result

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting Order details -> {str(e)}",
            )

    async def get_order(self, order_id: str, session: AsyncSession):
        try:
            statement = select(Order).where(Order.uid == order_id)
            result = await session.exec(statement)
            order = result.one()
            return order
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting Order details: {str(e)}",
            )

    async def create_Order(
        self, customer_id: uuid.UUID, order_details: OrderSchema, session: AsyncSession
    ):
        try:
            order_details_dict = order_details.model_dump()
            order_details_dict["customer_id"] = customer_id
            new_order = Order(**order_details_dict)
            session.add(new_order)
            await session.commit()
            await session.refresh(new_order)
            return new_order
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error Creating New Order : -> {str(e)}",
            )

    # Create Order Item Entry
    async def create_Items_Order_list(
        self, order_items_list: Order_Items_Schema, session: AsyncSession
    ):
        try:
            order_id = order_items_list.order_id
            order_in_db = await self.get_order(order_id=order_id, session=session)
            if order_in_db is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Order with id {str(order_id)} not found in the database",
                )
            items_list: List[Item_Quantity] = order_items_list.items
            order_item_final_list: List = []
            for order_detail in items_list:
                order_info = order_detail.model_dump()
                item_info = await item_service.get_item(order_detail.item_id, session)
                if item_info is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Error getting Item information with id {str(order_detail.item_id)}",
                    )
                order_price = round(item_info.price * order_detail.quantity, 2)
                new_order_item = Order_Items(
                    order_id=order_id, **order_info, price_at_order_time=order_price
                )
                session.add(new_order_item)
                await session.commit()
                await session.refresh(new_order_item)
                order_item_final_list.append(convert_str(new_order_item.model_dump()))
            return order_item_final_list
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error Creating Orders: {str(e)}",
            )

    async def update_orders(
        self,
        order: Order,
        updated_order_details: UpdateOrderSchema,
        session: AsyncSession,
    ):
        try:
            updated_order_dict = updated_order_details.model_dump(exclude_unset=True)
            print("UPDATED DICT : ", updated_order_dict)
            if (
                updated_order_dict.get("delivery_type") == "home_delivery"
                and updated_order_dict.get("address_id") is None
            ):
                if order.address_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                        detail=f"Address id cannot be null when Delivery is of Home Delivery",
                    )
            for key, value in updated_order_dict.items():
                if hasattr(order, key):
                    setattr(order, key, value)
                else:
                    raise ValueError(f"Invalid key attribute: {str(key)}")
            await session.commit()
            await session.refresh(order)
            return order
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error Updating Order -> {str(e)}",
            )

    async def cancel_orders(
        self,
        order: Order,
        session: AsyncSession,
    ):
        try:
            order.order_status = OrderStatus.CANCELLED
            await session.commit()
            # await session.refresh(order)
            return True
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error Updating Order -> {str(e)}",
            )

    # Update everything in a Order except the Delivery Type
    # Update of address_id is only for the Staffs
    # Cancel Order for only User Itself and Manager or the Admin
    # Only the Manager and Admin can delete Orders
    # User with Customer can only change the Delivery Status to Cancelled. Not anything else
    # User with Staff type can change everything but not to cancelled.
