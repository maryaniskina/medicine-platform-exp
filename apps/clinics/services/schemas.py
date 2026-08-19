from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StrictBool

NonEmptyString = Annotated['str', Field(min_length=1)]


class ClinicEventData(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        str_strip_whitespace=True,
    )

    external_id: NonEmptyString = Field(max_length=100)
    name: NonEmptyString = Field(max_length=255)
    address: NonEmptyString = Field(max_length=500)
    latitude: Decimal = Field(
        ge=Decimal('-90'),
        le=Decimal('90'),
        max_digits=9,
        decimal_places=6,
    )
    longitude: Decimal = Field(
        ge=Decimal('-180'),
        le=Decimal('180'),
        max_digits=9,
        decimal_places=6,
    )
    phone: 'str' = Field(default='', max_length=32)
    email: EmailStr | Literal[''] = ''
    is_active: StrictBool = True


class ClinicEvent(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        str_strip_whitespace=True,
    )

    event_id: NonEmptyString = Field(max_length=100)
    event_type: Literal['clinic.created', 'clinic.updated']
    version: Literal[1]
    data: ClinicEventData
