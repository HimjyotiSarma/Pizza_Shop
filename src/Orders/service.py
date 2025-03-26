from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
from src.db.models import Order, Order_Items
from typing import List
from .schemas import OrderSchema, Order_Items_Schema, Item_Quantity
from src.items_Categories.service import ItemService

item_service = ItemService()


class OrderService:
    async def get_order(self, order_id: str, session: AsyncSession):
        try:
            statement = select(Order).where(Order.uid == order_id)
            result = await session.exec(statement)
            order = result.first()
            return order
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error gettind Order details: {str(e)}",
            )

    async def create_Order(self, order_details: OrderSchema, session: AsyncSession):
        try:
            order_details_dict = order_details.model_dump()
            new_order = Order(**order_details_dict)
            session.add(new_order)
            await session.commit()
            await session.refresh(new_order)
            return new_order
        except Exception as e:
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
                order_item_final_list.append(new_order_item)
            return order_item_final_list
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error Creating Orders: {str(e)}",
            )

    # Update Only the Address for User with role Customer
    # Update everything in a Order except the Delivery Type
    # Cancel Order for only User Itself and Manager or the Admin
