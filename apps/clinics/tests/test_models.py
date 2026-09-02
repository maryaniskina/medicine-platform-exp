import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.clinics.models import Clinic


@pytest.mark.django_db
class TestClinicModel:
    def test_create_clinic(self, clinic_factory):
        clinic = clinic_factory()

        assert clinic.pk is not None
        assert clinic.external_id == 'clinic-001'
        assert clinic.name == 'Клиника № 1'
        assert clinic.address == 'Москва, Тверская улица, 1'
        assert str(clinic) == 'Клиника № 1'

    def test_active_by_default(self, clinic_factory):
        clinic = clinic_factory()

        assert clinic.is_active is True

    def test_optional_contacts_default_to_empty_strings(
        self,
        clinic_factory,
    ):
        clinic = clinic_factory(phone='', email='')

        assert clinic.phone == ''
        assert clinic.email == ''

    def test_timestamps_are_set(self, clinic_factory):
        clinic = clinic_factory()

        assert clinic.created_at is not None
        assert clinic.updated_at is not None

    def test_external_id_must_be_unique(self, clinic_factory):
        clinic_factory()

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                clinic_factory(
                    external_id='clinic-001',
                    name='Другая клиника',
                )

    @pytest.mark.parametrize('latitude', ['-90', '0', '90'])
    def test_valid_latitude(self, clinic_factory, latitude):
        clinic = clinic_factory(latitude=latitude)

        clinic.full_clean()

    @pytest.mark.parametrize(
        'latitude',
        ['-90.000001', '90.000001'],
    )
    def test_invalid_latitude(self, clinic_factory, latitude):
        clinic = clinic_factory(latitude=latitude)

        with pytest.raises(ValidationError):
            clinic.full_clean()

    @pytest.mark.parametrize('longitude', ['-180', '0', '180'])
    def test_valid_longitude(self, clinic_factory, longitude):
        clinic = clinic_factory(longitude=longitude)

        clinic.full_clean()

    @pytest.mark.parametrize(
        'longitude',
        ['-180.000001', '180.000001'],
    )
    def test_invalid_longitude(self, clinic_factory, longitude):
        clinic = clinic_factory(longitude=longitude)

        with pytest.raises(ValidationError):
            clinic.full_clean()

    def test_default_ordering_is_by_name(self, clinic_factory):
        clinic_factory()
        clinic_factory(
            external_id='clinic-002',
            name='Яблоко',
        )
        clinic_factory(
            external_id='clinic-003',
            name='Альфа',
        )

        clinics = list(Clinic.objects.values_list('name', flat=True))

        assert clinics == ['Альфа', 'Клиника № 1', 'Яблоко']
