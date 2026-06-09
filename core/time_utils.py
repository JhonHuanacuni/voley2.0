from datetime import date, datetime, time

from django.utils import timezone


def local_datetime_range(start_date: date, end_date: date):
    """Rango aware en hora de Perú (TIME_ZONE del proyecto) para filtrar DateTimeField."""
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(start_date, time.min), tz)
    end = timezone.make_aware(datetime.combine(end_date, time.max), tz)
    return start, end


def local_datetime_from(date_value: date):
    start, _ = local_datetime_range(date_value, date_value)
    return start
