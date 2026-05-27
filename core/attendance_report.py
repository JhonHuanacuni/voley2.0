from datetime import date, timedelta
import calendar

from .models import Attendance, Shift, Student


def _weekday_from_date(date_string):
    try:
        selected = date.fromisoformat(date_string)
    except (TypeError, ValueError):
        return None
    return selected.weekday() + 1 if selected.weekday() < 6 else 0


def _student_attends_on_date(student, date_string):
    weekday = _weekday_from_date(date_string)
    if weekday is None:
        return True
    days = student.attendance_days or []
    if not days or len(days) == 7:
        return True
    return weekday in days


def _shift_active_on_date(shift, date_string):
    if not shift:
        return True
    return shift.is_active_on_weekday(_weekday_from_date(date_string))


def week_bounds(reference: date):
    """Lunes a domingo de la semana que contiene la fecha de referencia."""
    monday = reference - timedelta(days=reference.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def month_bounds(reference: date):
    _, last_day = calendar.monthrange(reference.year, reference.month)
    return date(reference.year, reference.month, 1), date(reference.year, reference.month, last_day)


def eligible_students_for_date(target_date, shift_id=None):
    date_str = target_date.isoformat()
    students = Student.objects.filter(retired=False, enrollment_status='active')
    if shift_id:
        students = students.filter(shift_id=shift_id)
    selected_shift = Shift.objects.filter(pk=shift_id).first() if shift_id else None
    return [
        student
        for student in students.select_related('shift').order_by('name')
        if _student_attends_on_date(student, date_str)
        and _shift_active_on_date(selected_shift, date_str)
    ]


def build_daily_report(target_date, shift_id=None):
    eligible = eligible_students_for_date(target_date, shift_id)
    student_ids = [student.id for student in eligible]
    records = {
        attendance.student_id: attendance
        for attendance in Attendance.objects.filter(date=target_date, student_id__in=student_ids)
    }

    present = []
    absent = []
    late = []
    not_marked = []

    for student in eligible:
        record = records.get(student.id)
        if not record:
            not_marked.append(student)
        elif record.status == 'present':
            present.append({'student': student, 'record': record})
        elif record.status == 'absent':
            absent.append({'student': student, 'record': record})
        elif record.status == 'late':
            late.append({'student': student, 'record': record})

    return {
        'period': 'daily',
        'date': target_date,
        'start_date': target_date,
        'end_date': target_date,
        'present': present,
        'absent': absent,
        'late': late,
        'not_marked': not_marked,
        'total_eligible': len(eligible),
        'present_count': len(present),
        'absent_count': len(absent),
        'late_count': len(late),
        'not_marked_count': len(not_marked),
    }


def build_range_report(start_date, end_date, shift_id=None, period='weekly'):
    daily_reports = []
    current = start_date
    while current <= end_date:
        daily_reports.append(build_daily_report(current, shift_id))
        current += timedelta(days=1)

    attendance_qs = Attendance.objects.filter(
        date__gte=start_date,
        date__lte=end_date,
    ).select_related('student', 'student__shift')
    if shift_id:
        attendance_qs = attendance_qs.filter(student__shift_id=shift_id)

    absent_records = list(
        attendance_qs.filter(status='absent').order_by('-date', 'student__name')
    )
    present_records = list(
        attendance_qs.filter(status='present').order_by('-date', 'student__name')
    )
    late_records = list(
        attendance_qs.filter(status='late').order_by('-date', 'student__name')
    )

    total_present = sum(day['present_count'] for day in daily_reports)
    total_absent = sum(day['absent_count'] for day in daily_reports)
    total_late = sum(day['late_count'] for day in daily_reports)
    total_not_marked = sum(day['not_marked_count'] for day in daily_reports)

    return {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'daily_reports': daily_reports,
        'absent_records': absent_records,
        'present_records': present_records,
        'late_records': late_records,
        'present_count': total_present,
        'absent_count': total_absent,
        'late_count': total_late,
        'not_marked_count': total_not_marked,
    }


def build_weekly_report(week_start, week_end, shift_id=None):
    return build_range_report(week_start, week_end, shift_id, period='weekly')


def build_monthly_report(month_start, month_end, shift_id=None):
    return build_range_report(month_start, month_end, shift_id, period='monthly')


def compute_percentage_stats(start_date, end_date, shift_id=None):
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    attendance_qs = Attendance.objects.filter(date__gte=start_date, date__lte=end_date)
    if shift_id:
        attendance_qs = attendance_qs.filter(student__shift_id=shift_id)

    present = attendance_qs.filter(status='present').count()
    absent = attendance_qs.filter(status='absent').count()
    late = attendance_qs.filter(status='late').count()
    total = present + absent + late

    if total == 0:
        return {
            'present': 0,
            'absent': 0,
            'late': 0,
            'total': 0,
            'present_pct': 0.0,
            'absent_pct': 0.0,
            'late_pct': 0.0,
            'start_date': start_date,
            'end_date': end_date,
        }

    return {
        'present': present,
        'absent': absent,
        'late': late,
        'total': total,
        'present_pct': round(present / total * 100, 1),
        'absent_pct': round(absent / total * 100, 1),
        'late_pct': round(late / total * 100, 1),
        'start_date': start_date,
        'end_date': end_date,
    }


def get_attendance_daily_series(reference_date, shift_id=None, today=None):
    """Conteo diario de asistencias, faltas y tardanzas (inicio de mes hasta hoy)."""
    today = today or date.today()
    month_start, month_end = month_bounds(reference_date)
    end_date = min(today, month_end)

    labels = []
    present_data = []
    absent_data = []
    late_data = []

    current = month_start
    while current <= end_date:
        qs = Attendance.objects.filter(date=current)
        if shift_id:
            qs = qs.filter(student__shift_id=shift_id)

        labels.append(current.strftime('%d/%m'))
        present_data.append(qs.filter(status='present').count())
        absent_data.append(qs.filter(status='absent').count())
        late_data.append(qs.filter(status='late').count())
        current += timedelta(days=1)

    return {
        'labels': labels,
        'present': present_data,
        'absent': absent_data,
        'late': late_data,
        'start_date': month_start,
        'end_date': end_date,
    }


def get_attendance_chart_stats(reference_date, shift_id=None, today=None):
    """Resumen acumulado (% ) y evolución diaria del mes hasta hoy."""
    today = today or date.today()
    month_start, month_end = month_bounds(reference_date)
    until_today_end = min(today, month_end)

    return {
        'until_today': compute_percentage_stats(month_start, until_today_end, shift_id),
        'daily_series': get_attendance_daily_series(reference_date, shift_id, today),
        'month_start': month_start,
        'month_end': month_end,
    }


def get_attendance_report(period, start_date, end_date=None, shift_id=None):
    shift_id = shift_id or None
    end_date = end_date or start_date

    if period == 'daily':
        return build_daily_report(start_date, shift_id)
    if period == 'weekly':
        if start_date == end_date:
            week_start, week_end = week_bounds(start_date)
        else:
            week_start, week_end = start_date, end_date
        return build_weekly_report(week_start, week_end, shift_id)
    if period == 'monthly':
        if start_date == end_date:
            month_start, month_end = month_bounds(start_date)
        else:
            month_start, month_end = start_date, end_date
        return build_monthly_report(month_start, month_end, shift_id)

    return build_range_report(start_date, end_date, shift_id, period='weekly')
