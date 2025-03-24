from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
from src.db.models import Order
from .schemas import OrderSchema


class OrderService:
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
    # async def
