from datetime import datetime, time, timedelta
from types import SimpleNamespace

import pytest
from django.utils import timezone

from apps.scheduling.services.availability import is_slot_in_schedule


@pytest.fixture
def schedule_data(booking_date):
    return SimpleNamespace(
        weekday=booking_date.weekday(),
        valid_from=booking_date,
        valid_until=None,
        start_time=time(9, 0),
        end_time=time(12, 0),
    )


def make_aware_slot(booking_date, start_time, duration_minutes=30):
    local_timezone = timezone.get_default_timezone()
    start_at = timezone.make_aware(
        datetime.combine(booking_date, start_time),
        local_timezone,
    )
    end_at = start_at + timedelta(minutes=duration_minutes)
    return start_at, end_at


def test_accepts_slot_aligned_with_schedule(booking_date, schedule_data):
    start_at, end_at = make_aware_slot(booking_date, time(10, 0))

    assert is_slot_in_schedule(
        schedules=[schedule_data],
        start_at=start_at,
        end_at=end_at,
        duration_minutes=30,
    )


def test_rejects_slot_not_aligned_with_duration(booking_date, schedule_data):
    start_at, end_at = make_aware_slot(booking_date, time(10, 15))

    assert not is_slot_in_schedule(
        schedules=[schedule_data],
        start_at=start_at,
        end_at=end_at,
        duration_minutes=30,
    )


def test_rejects_slot_outside_schedule(booking_date, schedule_data):
    start_at, end_at = make_aware_slot(booking_date, time(12, 0))

    assert not is_slot_in_schedule(
        schedules=[schedule_data],
        start_at=start_at,
        end_at=end_at,
        duration_minutes=30,
    )


def test_rejects_slot_on_wrong_weekday(booking_date, schedule_data):
    next_date = booking_date + timedelta(days=1)
    start_at, end_at = make_aware_slot(next_date, time(10, 0))

    assert not is_slot_in_schedule(
        schedules=[schedule_data],
        start_at=start_at,
        end_at=end_at,
        duration_minutes=30,
    )


def test_rejects_slot_outside_schedule_validity(booking_date, schedule_data):
    schedule_data.valid_until = booking_date - timedelta(days=1)
    start_at, end_at = make_aware_slot(booking_date, time(10, 0))

    assert not is_slot_in_schedule(
        schedules=[schedule_data],
        start_at=start_at,
        end_at=end_at,
        duration_minutes=30,
    )


def test_rejects_naive_datetime(booking_date, schedule_data):
    start_at = datetime.combine(booking_date, time(10, 0))
    end_at = datetime.combine(booking_date, time(10, 30))

    assert not is_slot_in_schedule(
        schedules=[schedule_data],
        start_at=start_at,
        end_at=end_at,
        duration_minutes=30,
    )


def test_rejects_end_before_start(booking_date, schedule_data):
    start_at, end_at = make_aware_slot(booking_date, time(10, 0))

    assert not is_slot_in_schedule(
        schedules=[schedule_data],
        start_at=end_at,
        end_at=start_at,
        duration_minutes=30,
    )


def test_rejects_slot_crossing_local_midnight(booking_date, schedule_data):
    local_timezone = timezone.get_default_timezone()
    start_at = timezone.make_aware(
        datetime.combine(booking_date, time(23, 45)),
        local_timezone,
    )
    end_at = start_at + timedelta(minutes=30)

    assert not is_slot_in_schedule(
        schedules=[schedule_data],
        start_at=start_at,
        end_at=end_at,
        duration_minutes=30,
    )
