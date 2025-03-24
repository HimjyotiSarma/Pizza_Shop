from fastapi import Form, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from typing_extensions import Annotated
from src.db.Types import Order_Size, Food_Type


class ItemSchema(BaseModel):
    name: str
    description: str
    sku: str
    size: Order_Size = Order_Size.MEDIUM
    price: Annotated[Decimal, Field(decimal_places=2, max_digits=10, default=0.00)]
    category: str


class ItemUpdateSchema(BaseModel):
    name: Optional[str]
    description: Optional[str]
    sku: Optional[str]
    size: Optional[Order_Size]
    price: Optional[Decimal]


class CategorySchema(BaseModel):
    name: str
    type_of: str | Food_Type = Food_Type.OTHER
    description: str = Annotated[
        str, Field(min_length=10, max_length=250, default="Descriprion not available")
    ]
