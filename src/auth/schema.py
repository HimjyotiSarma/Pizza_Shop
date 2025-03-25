from pydantic import BaseModel, constr, EmailStr, conint, StringConstraints, Field
from src.db.Types import User_Roles
from typing import Optional
import uuid

# from typing import
from typing_extensions import Annotated


class UserSchema(BaseModel):
    firstname: Annotated[str, Field(min_length=2, max_length=30, examples=["Rahul"])]
    lastname: Annotated[
        Optional[str],
        Field(min_length=2, max_length=30, examples=["Verma"], default=None),
    ]
    email: EmailStr
    phone: Annotated[
        str,
        Field(
            min_length=10,
            max_length=10,
            pattern=r"^[6-9]\d{9}$",
            examples=["9876543210"],
        ),
    ]
    password: Annotated[
        str,
        Field(
            min_length=8,
            max_length=20,
            pattern=r"^[A-Za-z\d@$!%*?&]{8,}$",
            examples=[
                "At least one uppercase letter, one lowercase, one digit, one special character (@$!%*?&) and atleast 8 character"
            ],
        ),
    ]


class UserUpdateSchema(BaseModel):
    firstname: Optional[Annotated[str, Field(min_length=2, max_length=30)]]
    lastname: Optional[
        Annotated[
            str,
            Field(min_length=2, max_length=30, examples=["Verma"], default=None),
        ]
    ]
    email: Optional[EmailStr]
    password: Optional[
        Annotated[
            str,
            Field(min_length=8, max_length=20, pattern=r"^[A-Za-z\d@$!%*?&]{8,}$"),
        ]
    ]


class UserRoleUpdate(BaseModel):
    role: User_Roles


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class EmailSchema(BaseModel):
    emails: list[EmailStr]
    subject: str
    body: str


class PasswordResetSchema(BaseModel):
    email_id: EmailStr


class PasswordConfirmSchema(BaseModel):
    new_password: str
    confirm_password: str


class Delivery_Address(BaseModel):
    customer_id: uuid.UUID
    address_line_1: Annotated[
        str,
        Field(
            min_length=10, max_length=200, examples=["24 Gandhi Nagar, 1st Cross Road"]
        ),
    ]
    address_line_2: Annotated[
        str, Field(min_length=10, max_length=200, examples=["Near Shivaji Circle"])
    ]
    city: Annotated[str, Field(min_length=3, max_length=50, examples=["Mumbai"])]
    postal_code: Annotated[
        str,
        Field(
            min_length=6, max_length=6, pattern=r"^[1-9][0-9]{5}$", examples=["400001"]
        ),
    ]
