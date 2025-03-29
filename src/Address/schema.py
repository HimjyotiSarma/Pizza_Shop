from pydantic import BaseModel, Field
from typing import Optional
import uuid


class AddressSchema(BaseModel):
    address_line_1: str = Field(
        ...,
        min_length=5,
        max_length=250,
        examples=["12 Gandhi Road"],
        description="Primary address line",
    )

    address_line_2: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=250,
        examples=["Shivaji Nagar"],
        description="Optional additional address details",
    )

    city: str = Field(
        ...,
        min_length=2,
        max_length=50,
        examples=["Mumbai"],
        description="City/District name",
        pattern=r"^[a-zA-Z\s\-\.]+$",  # Allows city names with spaces, hyphens, and dots
    )

    postal_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        examples=["400001", "560001"],
        description="6-digit Indian PIN code",
        pattern=r"^[1-9][0-9]{5}$",  # Indian PIN code validation
    )


class UpdateAddressSchema(BaseModel):
    address_line_1: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=250,
        examples=["12 Gandhi Road"],
        description="Primary address line",
    )

    address_line_2: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=250,
        examples=["Shivaji Nagar"],
        description="Optional additional address details",
    )

    city: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
        examples=["Mumbai"],
        description="City/District name",
        pattern=r"^[a-zA-Z\s\-\.]+$",  # Allows city names with spaces, hyphens, and dots
    )

    postal_code: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=6,
        examples=["400001", "560001"],
        description="6-digit Indian PIN code",
        pattern=r"^[1-9][0-9]{5}$",  # Indian PIN code validation
    )
