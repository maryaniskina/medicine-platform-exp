import pytest

from apps.clinics.serializers import ClinicSerializer


@pytest.mark.django_db
class TestClinicSerializer:
    def test_serializes_public_fields(self, clinic_factory):
        clinic = clinic_factory()

        data = ClinicSerializer(clinic).data

        assert data['id'] == clinic.pk
        assert data['name'] == 'Клиника № 1'
        assert data['address'] == 'Москва, Тверская улица, 1'
        assert data['latitude'] == '55.765123'
        assert data['longitude'] == '37.605678'
        assert data['phone'] == '+74950000000'
        assert data['email'] == 'clinic@example.com'

    def test_does_not_expose_external_id(self, clinic_factory):
        clinic = clinic_factory()

        data = ClinicSerializer(clinic).data

        assert 'external_id' not in data

    def test_does_not_expose_internal_fields(self, clinic_factory):
        clinic = clinic_factory()

        data = ClinicSerializer(clinic).data

        assert 'created_at' not in data
        assert 'updated_at' not in data
        assert 'is_active' not in data

    def test_all_public_fields_are_read_only(self, clinic_factory):
        clinic = clinic_factory()
        serializer = ClinicSerializer(
            clinic,
            data={
                'name': 'Изменённое название',
                'address': 'Другой адрес',
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {}

    def test_serializes_multiple_clinics(self, clinic_factory):
        first = clinic_factory()
        second = clinic_factory(
            external_id='clinic-002',
            name='Клиника № 2',
        )

        serializer = ClinicSerializer([first, second], many=True)

        assert len(serializer.data) == 2
        assert serializer.data[0]['name'] == 'Клиника № 1'
        assert serializer.data[1]['name'] == 'Клиника № 2'
