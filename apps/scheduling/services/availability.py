from datetime import datetime, timedelta

from django.utils import timezone


def is_slot_in_schedule(
    *,
    schedules,
    start_at: datetime,
    end_at: datetime,
    duration_minutes: int,
) -> bool:
    if (
        not timezone.is_aware(start_at)
        or not timezone.is_aware(end_at)
        or end_at <= start_at
    ):
        return False

    local_timezone = timezone.get_default_timezone()
    local_start = timezone.localtime(start_at, local_timezone)
    local_end = timezone.localtime(end_at, local_timezone)

    if local_start.date() != local_end.date():
        return False

    start = local_start.replace(tzinfo=None)
    end = local_end.replace(tzinfo=None)
    duration = timedelta(minutes=duration_minutes)

    if end - start != duration:
        return False

    for schedule in schedules:
        if schedule.weekday != local_start.weekday():
            continue

        if not (
            schedule.valid_from <= local_start.date()
            and (
                schedule.valid_until is None
                or schedule.valid_until >= local_start.date()
            )
        ):
            continue

        schedule_start = datetime.combine(
            local_start.date(),
            schedule.start_time,
        )
        schedule_end = datetime.combine(
            local_start.date(),
            schedule.end_time,
        )

        if not (schedule_start <= start and end <= schedule_end):
            continue

        elapsed = start - schedule_start

        if elapsed.total_seconds() % duration.total_seconds() == 0:
            return True

    return False
