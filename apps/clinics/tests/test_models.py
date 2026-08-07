import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.clinics.models import Clinic


@pytest.mark.django_db
class TestClinicModel:
    def create_clinic(self, **overrides):
        data = {
            'external_id': 'clinic-001',
            'name': 'Клиника № 1',
            'address': 'Москва, Тверская улица, 1',
            'latitude': '55.765123',
            'longitude': '37.605678',
            'phone': '+74950000000',
            'email': 'clinic@example.com',
        }
        data.update(overrides)
        return Clinic.objects.create(**data)

    def test_create_clinic(self):
        clinic = self.create_clinic()

        assert clinic.pk is not None
        assert clinic.external_id == 'clinic-001'
        assert clinic.name == 'Клиника № 1'
        assert clinic.address == 'Москва, Тверская улица, 1'
        assert str(clinic) == 'Клиника № 1'

    def test_active_by_default(self):
        clinic = self.create_clinic()

        assert clinic.is_active is True

    def test_optional_contacts_default_to_empty_strings(self):
        clinic = self.create_clinic(phone='', email='')

        assert clinic.phone == ''
        assert clinic.email == ''

    def test_timestamps_are_set(self):
        clinic = self.create_clinic()

        assert clinic.created_at is not None
        assert clinic.updated_at is not None

    def test_external_id_must_be_unique(self):
        self.create_clinic()

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                self.create_clinic(
                    name='Другая клиника',
                    external_id='clinic-001',
                )

    @pytest.mark.parametrize(
        'latitude',
        ['-90', '0', '90'],
    )
    def test_valid_latitude(self, latitude):
        clinic = self.create_clinic(latitude=latitude)

        clinic.full_clean()

    @pytest.mark.parametrize(
        'latitude',
        ['-90.000001', '90.000001'],
    )
    def test_invalid_latitude(self, latitude):
        clinic = self.create_clinic(latitude=latitude)

        with pytest.raises(ValidationError):
            clinic.full_clean()

    @pytest.mark.parametrize(
        'longitude',
        ['-180', '0', '180'],
    )
    def test_valid_longitude(self, longitude):
        clinic = self.create_clinic(longitude=longitude)

        clinic.full_clean()

    @pytest.mark.parametrize(
        'longitude',
        ['-180.000001', '180.000001'],
    )
    def test_invalid_longitude(self, longitude):
        clinic = self.create_clinic(longitude=longitude)

        with pytest.raises(ValidationError):
            clinic.full_clean()

    def test_default_ordering_is_by_name(self):
        self.create_clinic(
            external_id='clinic-002',
            name='Яблоко',
        )
        self.create_clinic(
            external_id='clinic-003',
            name='Альфа',
        )

        clinics = list(Clinic.objects.values_list('name', flat=True))

        assert clinics == ['Альфа', 'Яблоко']
