from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    AliasChoices,
    AnyUrl,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)

NonEmptyString = Annotated[str, Field(min_length=1)]


class DoctorClinicEventData(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

    external_id: NonEmptyString = Field(max_length=100)
    price: Decimal | None = Field(
        default=None,
        ge=Decimal('0'),
        max_digits=10,
        decimal_places=2,
    )
    duration_minutes: int = Field(default=30, ge=5, le=240)


class DoctorEventData(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

    external_id: NonEmptyString = Field(max_length=100)
    first_name: NonEmptyString = Field(max_length=150)
    last_name: NonEmptyString = Field(max_length=150)
    middle_name: str = Field(
        default='',
        max_length=150,
        validation_alias=AliasChoices('middle_name', 'patronymic'),
    )
    email: EmailStr
    photo_url: AnyUrl | Literal[''] = ''
    description: str = ''
    years_of_experience: int = Field(default=0, ge=0, le=32767)
    specializations: list[NonEmptyString] = Field(default_factory=list)
    clinics: list[DoctorClinicEventData] = Field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def accept_patronymic_when_middle_name_is_null(cls, value):
        if (
            isinstance(value, dict)
            and value.get('middle_name') is None
            and 'patronymic' in value
        ):
            value = value.copy()
            value.pop('middle_name')
        return value

    @model_validator(mode='after')
    def validate_unique_associations(self) -> 'DoctorEventData':
        clinic_ids = [clinic.external_id for clinic in self.clinics]
        if len(clinic_ids) != len(set(clinic_ids)):
            raise ValueError('Duplicate clinic external_id')

        specialization_names = self.specializations
        if len(specialization_names) != len(set(specialization_names)):
            raise ValueError('Duplicate specialization names')

        return self


class DoctorEvent(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

    event_id: NonEmptyString
    event_type: NonEmptyString
    version: int = Field(ge=1)
    data: DoctorEventData
