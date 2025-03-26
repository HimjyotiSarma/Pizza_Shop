from pydantic import BaseModel, NonNegativeInt, condecimal, Field, model_validator
from typing_extensions import Annotated, Self
from typing import List, Optional
from datetime import datetime, date
import uuid
from decimal import Decimal

# Order Types, Delivery Types, Order Size
from src.db.Types import (
    Delivery_Type,
    OrderStatus,
    Order_Size,
    Payment_Method,
    Payment_Status,
)


# Main Order Schemas


# order_status: OrderStatus = Field(default=OrderStatus.PROCESSING)


# NOTE -> Address Id can be None and For Empty address Id the delivery type is PICKUP
class OrderSchema(BaseModel):
    customer_id: uuid.UUID
    address_id: Optional[uuid.UUID] = None
    delivery_type: Delivery_Type = Field(default=Delivery_Type.HOME_DELIVERY)

    @model_validator(mode="before")
    @classmethod
    def validate_delivery(cls, values) -> Self:
        if (
            values.get("delivery_type") == Delivery_Type.HOME_DELIVERY
            and values.get("address_id") is None
        ):
            raise ValueError("The Address Field cannot be empty for Home Delivery")
        return values


class Item(BaseModel):
    name: str
    sku: str
    size: Order_Size = Field(default=Order_Size.MEDIUM)


# Each Order can can multiple Items and Each Item can have multiple Orders
# So we are using Order_Items


class Item_Quantity(BaseModel):
    item_id: uuid.UUID
    quantity: NonNegativeInt = Field(default=1, le=1, ge=100)


class Order_Items_Schema(BaseModel):
    order_id: uuid.UUID
    items: List[Item_Quantity]
    # price_at_order_time: Decimal = Field(
    #     default=Decimal("0.00"), max_digits=10, decimal_places=2, examples=[12.99]
    # )


class Pizza_Category(BaseModel):
    name: str = Field(min_length=2, max_length=50, examples=["Vegetarian Pizzas"])
    description: str = Field(..., min_length=10, max_length=500)


class Item_Category(BaseModel):
    item_id: uuid.UUID
    category_id: uuid.UUID


class Payment(BaseModel):
    order_id: uuid.UUID
    payment_method: Payment_Method | str
    payment_status: Payment_Status = Field(default=Payment_Status.PENDING)
    amount: Decimal = Field(max_digits=10, decimal_places=2, examples=[24.99])
    transaction_id: Annotated[str, Field(max_length=256)]
    created_at: datetime = Field(default_factory=datetime.now)
