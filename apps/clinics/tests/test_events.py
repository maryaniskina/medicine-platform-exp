from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.clinics.models import Clinic
from apps.clinics.services.events import (
    ClinicEventError,
    parse_clinic_data,
    process_clinic_event,
)
from apps.events.exceptions import PermanentEventError
from apps.events.models import ProcessedMessage


def make_event(
    event_id: 'str' = 'evt-001',
    event_type: 'str' = 'clinic.created',
    **data_overrides,
) -> dict:
    data = {
        'external_id': 'clinic-001',
        'name': 'Клиника № 1',
        'address': 'Москва, Тверская улица, 1',
        'latitude': '55.765123',
        'longitude': '37.605678',
        'phone': '+74950000000',
        'email': 'clinic@example.com',
    }
    data.update(data_overrides)

    return {
        'event_id': event_id,
        'event_type': event_type,
        'version': 1,
        'data': data,
    }


@pytest.mark.django_db
class TestParseClinicData:
    def test_parses_valid_data(self):
        data = parse_clinic_data(make_event()['data'])

        assert data['external_id'] == 'clinic-001'
        assert data['latitude'] == Decimal('55.765123')
        assert data['longitude'] == Decimal('37.605678')

    def test_strips_whitespace_from_text_fields(self):
        data = parse_clinic_data(
            {
                **make_event()['data'],
                'external_id': ' clinic-001 ',
                'name': ' Клиника № 1 ',
                'address': ' Москва ',
            }
        )

        assert data['external_id'] == 'clinic-001'
        assert data['name'] == 'Клиника № 1'
        assert data['address'] == 'Москва'

    @pytest.mark.parametrize(
        'field',
        ['external_id', 'name', 'address', 'latitude', 'longitude'],
    )
    def test_requires_mandatory_fields(self, field):
        data = make_event()['data']
        del data[field]

        with pytest.raises(ClinicEventError):
            parse_clinic_data(data)

    @pytest.mark.parametrize('value', ['', '   '])
    def test_rejects_empty_required_text(self, value):
        with pytest.raises(ClinicEventError):
            parse_clinic_data(make_event(name=value)['data'])

    @pytest.mark.parametrize(
        ('field', 'value'),
        [
            ('latitude', '91'),
            ('latitude', '-91'),
            ('longitude', '181'),
            ('longitude', '-181'),
            ('latitude', 'not-a-number'),
            ('longitude', 'NaN'),
            ('latitude', 'Infinity'),
        ],
    )
    def test_rejects_invalid_coordinates(self, field, value):
        with pytest.raises(ClinicEventError):
            parse_clinic_data(make_event(**{field: value})['data'])

    @pytest.mark.parametrize('field', ['phone', 'email'])
    def test_optional_contacts_default_to_empty_strings(self, field):
        data = make_event()['data']
        data.pop(field)

        parsed = parse_clinic_data(data)

        assert parsed[field] == ''

    def test_rejects_non_string_phone(self):
        with pytest.raises(ClinicEventError):
            parse_clinic_data(make_event(phone=123)['data'])

    def test_rejects_non_string_email(self):
        with pytest.raises(ClinicEventError):
            parse_clinic_data(make_event(email=123)['data'])

    def test_rejects_non_boolean_is_active(self):
        with pytest.raises(ClinicEventError):
            parse_clinic_data(make_event(is_active='false')['data'])


@pytest.mark.django_db
class TestProcessClinicEvent:
    def test_creates_clinic_and_processed_message(self):
        result = process_clinic_event(make_event())

        clinic = Clinic.objects.get(external_id='clinic-001')

        assert result is True
        assert clinic.name == 'Клиника № 1'
        assert ProcessedMessage.objects.filter(event_id='evt-001').exists()

    def test_duplicate_event_is_ignored(self):
        event = make_event()

        assert process_clinic_event(event) is True
        assert process_clinic_event(event) is False

        assert Clinic.objects.count() == 1
        assert ProcessedMessage.objects.count() == 1

    def test_duplicate_event_does_not_overwrite_clinic(self):
        process_clinic_event(make_event())

        duplicate = make_event(name='Другое название')
        result = process_clinic_event(duplicate)

        clinic = Clinic.objects.get(external_id='clinic-001')

        assert result is False
        assert clinic.name == 'Клиника № 1'

    def test_different_event_can_create_another_clinic(self):
        process_clinic_event(make_event())

        event = make_event(
            event_id='evt-002',
            external_id='clinic-002',
            name='Клиника № 2',
        )
        process_clinic_event(event)

        assert Clinic.objects.count() == 2

    def test_invalid_coordinates_do_not_create_processed_message(self):
        event = make_event(latitude='100')

        with pytest.raises(ClinicEventError):
            process_clinic_event(event)

        assert Clinic.objects.count() == 0
        assert ProcessedMessage.objects.count() == 0

    def test_existing_external_id_rolls_back_processed_message(self):
        process_clinic_event(make_event())

        duplicate_clinic = make_event(
            event_id='evt-002',
            name='Дубликат',
        )

        with pytest.raises(PermanentEventError):
            process_clinic_event(duplicate_clinic)

        assert Clinic.objects.count() == 1
        assert not ProcessedMessage.objects.filter(
            event_id='evt-002',
        ).exists()

    def test_updates_existing_clinic(self):
        process_clinic_event(make_event())

        event = make_event(
            event_id='evt-002',
            event_type='clinic.updated',
            name='Обновлённая клиника',
            phone='+74951111111',
        )
        result = process_clinic_event(event)

        clinic = Clinic.objects.get(external_id='clinic-001')

        assert result is True
        assert Clinic.objects.count() == 1
        assert clinic.name == 'Обновлённая клиника'
        assert clinic.phone == '+74951111111'

    def test_update_of_missing_clinic_is_rejected(self):
        event = make_event(
            event_type='clinic.updated',
            external_id='missing-clinic',
        )

        with pytest.raises(PermanentEventError):
            process_clinic_event(event)

        assert Clinic.objects.count() == 0
        assert ProcessedMessage.objects.count() == 0

    def test_unsupported_event_type_is_rejected(self):
        event = make_event(event_type='clinic.deleted')

        with pytest.raises(PermanentEventError):
            process_clinic_event(event)

        assert Clinic.objects.count() == 0
        assert ProcessedMessage.objects.count() == 0

    def test_invalid_email_rolls_back_event(self):
        event = make_event(email='not-an-email')

        with pytest.raises(ClinicEventError):
            process_clinic_event(event)

        assert Clinic.objects.count() == 0
        assert ProcessedMessage.objects.count() == 0
