from django.shortcuts import render
from django.db.models import Count, Sum
from .models import Student, Attendance, Payment


def dashboard_view(request):
    students = Student.objects.all()
    active_students = students.filter(retired=False)
    retired_students = students.filter(retired=True)
    attendance_today = Attendance.objects.filter(date__exact=request.GET.get('date')) if request.GET.get('date') else Attendance.objects.none()
    total_payments = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    due_count = sum(1 for s in active_students if s.debt_info['debt'] and s.debt_info['debt'] > 0)

    context = {
        'active_count': active_students.count(),
        'retired_count': retired_students.count(),
        'attendance_count': attendance_today.count(),
        'payments_total': total_payments,
        'debt_count': due_count,
        'students': students,
    }
    return render(request, 'core/dashboard.html', context)
