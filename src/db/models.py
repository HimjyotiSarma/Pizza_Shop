from sqlmodel import Field, SQLModel, Column, Relationship
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy.schema import ForeignKey
from sqlalchemy import UniqueConstraint, func
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
import uuid


# Custom Types
from src.db.Types import (
    Delivery_Type,
    OrderStatus,
    Order_Size,
    Food_Type,
    Payment_Method,
    Payment_Status,
    User_Roles,
    Staff_Roles,
)


class Item_Category(SQLModel, table=True):
    __tablename__ = "itemCategories"
    item_id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, ForeignKey("items.uid", ondelete="CASCADE"), primary_key=True
        )
    )
    category_id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, ForeignKey("categories.uid", ondelete="CASCADE"), primary_key=True
        )
    )
    __table_args__ = (
        UniqueConstraint("item_id", "category_id", name="uq_item_category"),
    )


class Order_Items(SQLModel, table=True):
    __tablename__ = "orderItems"
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID, default=uuid.uuid4, primary_key=True)
    )
    order_id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, ForeignKey("orders.uid", ondelete="CASCADE"), nullable=False
        )
    )
    item_id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, ForeignKey("items.uid", ondelete="CASCADE"), nullable=False
        )
    )
    quantity: int = Field(sa_column=Column(pg.INTEGER, default=1, nullable=False))
    price_at_order_time: Decimal = Field(
        sa_column=Column(pg.NUMERIC(10, 2), nullable=False)
    )
    order: Optional["Order"] = Relationship(
        back_populates="order_items", sa_relationship_kwargs={"lazy": "selectin"}
    )
    item: Optional["Item"] = Relationship()


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID, primary_key=True, default=uuid.uuid4, nullable=False)
    )
    customer_id: uuid.UUID = Field(
        sa_column=Column(pg.UUID, ForeignKey("customers.uid", ondelete="SET NULL"))
    )
    delivery_type: Delivery_Type = Field(
        sa_column=Column(
            pg.ENUM(Delivery_Type), default=Delivery_Type.HOME_DELIVERY, nullable=False
        )
    )
    order_status: OrderStatus = Field(
        sa_column=Column(
            pg.ENUM(OrderStatus), default=OrderStatus.PROCESSING, nullable=False
        )
    )
    address_id: Optional[uuid.UUID] = Field(
        sa_column=Column(pg.UUID, ForeignKey("delivery_addresses.uid"), nullable=True)
    )
    customer: Optional["Customer"] = Relationship(
        back_populates="orders", sa_relationship_kwargs={"lazy": "selectin"}
    )
    order_items: List["Order_Items"] = Relationship(
        back_populates="order", sa_relationship_kwargs={"lazy": "selectin"}
    )
    created_at: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True), nullable=False, default=func.now()
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            default=func.now(),
            onupdate=func.now(),
        )
    )

    def __repr__(self):
        return f"<Order for Customer Id: {self.customer_id} with Order Id: {self.uid}"


# ADD IS_VERIFIED Field in Customer


class User(SQLModel, table=True):
    __tablename__ = "users"
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID, default=uuid.uuid4, primary_key=True)
    )
    firstname: str = Field(sa_column=Column(pg.VARCHAR(length=100), nullable=False))
    lastname: str = Field(sa_column=Column(pg.VARCHAR(length=100), nullable=True))
    email: str = Field(
        sa_column=Column(pg.VARCHAR(length=100), nullable=False, unique=True)
    )
    phone: str = Field(
        sa_column=Column(pg.VARCHAR(length=20), nullable=False, unique=True)
    )
    password_hash: str = Field(sa_column=Column(pg.VARCHAR(255), nullable=False))
    role: User_Roles | str = Field(
        sa_column=Column(
            pg.ENUM(User_Roles), default=User_Roles.CUSTOMER, nullable=False
        )
    )
    customer: Optional["Customer"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    staff: Optional["Staff"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    created_at: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True), nullable=False, default=func.now()
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            default=datetime.now,
            onupdate=func.now(),
        )
    )

    def __repr__(self):
        return f"<User {self.uid} and Name {self.firstname} {self.lastname}>"


class Customer(SQLModel, table=True):
    __tablename__ = "customers"
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID, default=uuid.uuid4, primary_key=True)
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            ForeignKey("users.uid", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        )
    )
    is_verified: bool = Field(
        sa_column=Column(pg.BOOLEAN, nullable=False, default=False)
    )
    user: User = Relationship(
        back_populates="customer", sa_relationship_kwargs={"lazy": "selectin"}
    )
    addresses: List["Delivery_Address"] = Relationship(
        back_populates="customer", sa_relationship_kwargs={"lazy": "selectin"}
    )
    orders: List[Order] = Relationship(
        back_populates="customer", sa_relationship_kwargs={"lazy": "selectin"}
    )

    def __repr__(self):
        return f"<Customer with id {self.uid} created>"


class Delivery_Address(SQLModel, table=True):
    __tablename__ = "delivery_addresses"
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID, default=uuid.uuid4, primary_key=True)
    )
    customer_id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, ForeignKey("customers.uid", ondelete="CASCADE"), nullable=False
        )
    )
    address_line_1: str = Field(sa_column=Column(pg.VARCHAR(250), nullable=False))
    address_line_2: Optional[str] = Field(
        sa_column=Column(pg.VARCHAR(250), nullable=True)
    )
    city: str = Field(sa_column=Column(pg.VARCHAR(100), nullable=True))
    postal_code: str = Field(sa_column=Column(pg.VARCHAR(100), nullable=True))
    customer: Optional[Customer] = Relationship(back_populates="addresses")

    def __repr__(self):
        return f"<Delivery_Address of Customer {self.customer_id}>"


class Staff(SQLModel, table=True):
    __tablename__ = "staffs"
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID, default=uuid.uuid4, primary_key=True)
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            ForeignKey("users.uid", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        )
    )
    job_title: Staff_Roles | str = Field(
        sa_column=Column(
            pg.ENUM(Staff_Roles), default=Staff_Roles.KITCHEN, nullable=False
        )
    )
    hire_date: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True), nullable=False, default=func.now()
        )
    )
    salary: Decimal = Field(
        sa_column=Column(pg.NUMERIC(10, 2), nullable=False, default=0.00)
    )
    user: User = Relationship(
        back_populates="staff", sa_relationship_kwargs={"lazy": "selectin"}
    )

    def __repr__(self):
        return f"<New Staff Added with role {self.job_title} and id {self.uid}"


class Item(SQLModel, table=True):
    __tablename__ = "items"
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID, default=uuid.uuid4, primary_key=True)
    )
    name: str = Field(sa_column=Column(pg.VARCHAR(250), nullable=False))
    description: str = Field(sa_column=Column(pg.VARCHAR(500), nullable=False))
    sku: str = Field(
        sa_column=Column(pg.VARCHAR(100), nullable=False, unique=True),
    )
    size: Order_Size | str = Field(
        sa_column=Column(pg.ENUM(Order_Size), default=Order_Size.MEDIUM, nullable=False)
    )
    price: Decimal = Field(
        sa_column=Column(pg.NUMERIC(10, 2), nullable=False, default=0.00)
    )
    image: str = Field(
        sa_column=Column(
            pg.VARCHAR(250),
            nullable=False,
            default="https://cksc.com.au/CKSC/media/Images/no-product-image-400x400.png",
        )
    )
    categories: list["Category"] = Relationship(
        back_populates="items",
        link_model=Item_Category,
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    # __table_args__=(
    #     UniqueConstraint("name", "sku", name="Unique_name_sku")
    # )

    def __repr__(self):
        return f"<Item {self.name} with SKU {self.sku}>"


class Category(SQLModel, table=True):
    __tablename__ = "categories"
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID, default=uuid.uuid4, primary_key=True)
    )
    name: str = Field(sa_column=Column(pg.VARCHAR(100), nullable=False, unique=True))
    type_of: Food_Type | str = Field(
        sa_column=Column(pg.ENUM(Food_Type), default=Food_Type.OTHER, nullable=False)
    )
    description: str = Field(sa_column=Column(pg.VARCHAR(250), nullable=False))
    image: str = Field(
        sa_column=Column(
            pg.VARCHAR(250),
            nullable=False,
            default="https://cksc.com.au/CKSC/media/Images/no-product-image-400x400.png",
        )
    )
    items: list["Item"] = Relationship(
        back_populates="categories",
        link_model=Item_Category,
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    def __repr__(self):
        return f"<Food Category {self.name} of Dish {self.type_of}>"


class Payment(SQLModel, table=True):
    __tablename__ = "payments"
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID, default=uuid.uuid4, primary_key=True)
    )
    transaction_id: str = Field(sa_column=Column(pg.VARCHAR(250), nullable=False))
    order_id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            ForeignKey("orders.uid", ondelete="SET NULL"),
        ),
    )
    payment_method: Payment_Method | str = Field(
        sa_column=Column(pg.ENUM(Payment_Method), nullable=False)
    )
    payment_status: Payment_Status | str = Field(
        sa_column=Column(
            pg.ENUM(Payment_Status), default=Payment_Status.PENDING, nullable=False
        )
    )
    amount: Decimal = Field(sa_column=Column(pg.NUMERIC(10, 2), nullable=False))
    created_at: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True), nullable=False, default=func.now()
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            default=func.now(),
            onupdate=func.now(),
        )
    )

    def __repr__(self):
        return f"<Payment {self.transaction_id} of Order {self.order_id}>"


# Create a Table of Categories and Link it to the Item by adding a  Connecting Table and using link_model
