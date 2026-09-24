from datetime import time, timedelta

import pytest
from django.core.exceptions import ValidationError

from apps.scheduling.models import WeeklySchedule


@pytest.mark.django_db
class TestWeeklyScheduleModel:
    def test_rejects_overlapping_schedule_for_same_weekday(
        self,
        booking_schedule,
    ):
        overlapping_schedule = WeeklySchedule(
            doctor_clinic=booking_schedule.doctor_clinic,
            weekday=booking_schedule.weekday,
            start_time=booking_schedule.start_time.replace(hour=10),
            end_time=booking_schedule.end_time,
            valid_from=booking_schedule.valid_from,
        )

        with pytest.raises(ValidationError, match='пересекается'):
            overlapping_schedule.full_clean()

    def test_allows_adjacent_schedule_intervals(self, booking_schedule):
        adjacent_schedule = WeeklySchedule(
            doctor_clinic=booking_schedule.doctor_clinic,
            weekday=booking_schedule.weekday,
            start_time=booking_schedule.end_time,
            end_time=booking_schedule.end_time.replace(hour=13),
            valid_from=booking_schedule.valid_from,
        )

        adjacent_schedule.full_clean()

    def test_rejects_end_date_before_start_date(
        self,
        booking_doctor_clinic,
        booking_date,
    ):
        schedule = WeeklySchedule(
            doctor_clinic=booking_doctor_clinic,
            weekday=booking_date.weekday(),
            start_time=booking_schedule_time(9),
            end_time=booking_schedule_time(10),
            valid_from=booking_date,
            valid_until=booking_date - timedelta(days=1),
        )

        with pytest.raises(ValidationError):
            schedule.full_clean()


def booking_schedule_time(hour):
    return time(hour, 0)
