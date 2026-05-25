import json
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import MembershipForm, MembershipRenewForm, PaymentForm
from .models import Membership, Payment, Student
from .receipt_pdf import fill_payment_receipt
from .views import get_user_role

MONTHS_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
}


def _membership_queryset():
    return Membership.objects.select_related('student', 'student__shift').order_by('-start_date', '-created_at')


def _is_secretary(user):
    return get_user_role(user) == 'secretary'


def _default_renew_end(start):
    if start.month == 12:
        return start.replace(year=start.year + 1, month=1, day=start.day)
    try:
        return start.replace(month=start.month + 1)
    except ValueError:
        return start + timedelta(days=30)


@login_required(login_url='login')
def membership_list(request):
    status_filter = request.GET.get('status', '')
    query = request.GET.get('q', '').strip()
    memberships = _membership_queryset()
    if status_filter in ('debt', 'completed'):
        memberships = memberships.filter(status=status_filter)
    if query:
        memberships = memberships.filter(
            Q(student__name__icontains=query)
            | Q(student__dni__icontains=query)
        )

    return render(request, 'core/memberships/list.html', {
        'memberships': memberships,
        'query': query,
        'status_filter': status_filter,
        'is_secretary': _is_secretary(request.user),
    })


@login_required(login_url='login')
def membership_create(request):
    form = MembershipForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('memberships_list')
    return render(request, 'core/memberships/list.html', {
        'memberships': _membership_queryset(),
        'form': form,
        'create_mode': True,
        'is_secretary': _is_secretary(request.user),
    })


@login_required(login_url='login')
def membership_edit(request, membership_id):
    membership = get_object_or_404(Membership, pk=membership_id)
    form = MembershipForm(request.POST or None, instance=membership)
    if request.method == 'POST' and form.is_valid():
        membership = form.save()
        membership.recalculate_status()
        return redirect('memberships_list')
    return render(request, 'core/memberships/list.html', {
        'memberships': _membership_queryset(),
        'form': form,
        'membership': membership,
        'edit_mode': True,
        'is_secretary': _is_secretary(request.user),
    })


@login_required(login_url='login')
def membership_delete(request, membership_id):
    if _is_secretary(request.user):
        return redirect('memberships_list')
    membership = get_object_or_404(Membership, pk=membership_id)
    membership.delete()
    return redirect('memberships_list')


@login_required(login_url='login')
def membership_renew(request, membership_id):
    old = get_object_or_404(Membership, pk=membership_id)
    default_start = old.end_date + timedelta(days=1) if old.end_date >= date.today() else date.today()
    default_end = _default_renew_end(default_start)
    initial = {
        'start_date': default_start,
        'end_date': default_end,
        'amount_due': old.student.monthly_fee or old.amount_due,
        'notes': f'Renovación de membresía #{old.pk}',
    }
    form = MembershipRenewForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        renewed = Membership.objects.create(
            student=old.student,
            start_date=form.cleaned_data['start_date'],
            end_date=form.cleaned_data['end_date'],
            amount_due=form.cleaned_data['amount_due'],
            notes=form.cleaned_data.get('notes') or '',
            renewed_from=old,
            status='debt',
        )
        renewed.recalculate_status()
        student = old.student
        student.membership_start = renewed.start_date
        student.membership_end = renewed.end_date
        student.save(update_fields=['membership_start', 'membership_end'])
        return redirect('memberships_list')
    return render(request, 'core/memberships/renew.html', {
        'form': form,
        'membership': old,
        'is_secretary': _is_secretary(request.user),
    })


@login_required(login_url='login')
def membership_payments(request, membership_id):
    membership = get_object_or_404(
        Membership.objects.select_related('student'),
        pk=membership_id,
    )
    payments = membership.payments.order_by('-date')
    form = PaymentForm(
        request.POST or None,
        membership_qs=Membership.objects.filter(pk=membership.pk),
    )
    if request.method == 'POST':
        form = PaymentForm(request.POST, membership_qs=Membership.objects.filter(pk=membership.pk))
        if form.is_valid():
            payment = form.save(commit=False)
            payment.membership = membership
            payment.student = membership.student
            payment.save()
            return redirect('membership_payments', membership_id=membership.pk)
    else:
        form.fields['membership'].initial = membership.pk

    return render(request, 'core/memberships/payments.html', {
        'membership': membership,
        'payments': payments,
        'form': form,
        'is_secretary': _is_secretary(request.user),
    })


@login_required(login_url='login')
def membership_payment_delete(request, membership_id, payment_id):
    if _is_secretary(request.user):
        return redirect('membership_payments', membership_id=membership_id)
    payment = get_object_or_404(Payment, pk=payment_id, membership_id=membership_id)
    membership = payment.membership
    payment.delete()
    if membership:
        membership.recalculate_status()
    return redirect('membership_payments', membership_id=membership_id)


@login_required(login_url='login')
def membership_payment_receipt(request, membership_id, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id, membership_id=membership_id)
    student = payment.student
    month_name = MONTHS_ES.get(payment.date.month, 'Desconocido')
    buffer = fill_payment_receipt(payment, student, month_name)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recibo_{payment.id}.pdf"'
    return response


@login_required(login_url='login')
def membership_payment_add(request):
    form = PaymentForm(request.POST or None, membership_qs=_membership_queryset())
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('membership_payments_list')
    return render(request, 'core/memberships/payments_list.html', {
        'payments': Payment.objects.select_related('membership', 'student').order_by('-date'),
        'memberships': _membership_queryset(),
        'form': form,
        'create_mode': True,
        'is_secretary': _is_secretary(request.user),
    })


@login_required(login_url='login')
def membership_payments_list(request):
    membership_filter = request.GET.get('membership', '')
    payments = Payment.objects.select_related('membership', 'membership__student', 'student').order_by('-date')
    if membership_filter:
        payments = payments.filter(membership_id=membership_filter)
    memberships = _membership_queryset()

    form = PaymentForm(
        request.POST or None,
        membership_qs=_membership_queryset(),
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        url = reverse('membership_payments_list')
        if membership_filter:
            url += f'?membership={membership_filter}'
        return redirect(url)

    return render(request, 'core/memberships/payments_list.html', {
        'payments': payments,
        'memberships': memberships,
        'form': form,
        'selected_membership': membership_filter,
        'create_mode': False,
        'is_secretary': _is_secretary(request.user),
    })


@login_required(login_url='login')
def membership_payment_edit(request, payment_id):
    payment = get_object_or_404(Payment.objects.select_related('membership'), pk=payment_id)
    membership_filter = request.GET.get('membership', '') or str(payment.membership_id or '')
    form = PaymentForm(
        request.POST or None,
        instance=payment,
        membership_qs=_membership_queryset(),
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        if payment.membership_id:
            return redirect('membership_payments', membership_id=payment.membership_id)
        url = reverse('membership_payments_list')
        if membership_filter:
            url += f'?membership={membership_filter}'
        return redirect(url)

    return render(request, 'core/memberships/payments_list.html', {
        'payments': Payment.objects.select_related('membership', 'student').order_by('-date'),
        'memberships': _membership_queryset(),
        'form': form,
        'payment': payment,
        'edit_mode': True,
        'selected_membership': membership_filter,
        'is_secretary': _is_secretary(request.user),
    })


@login_required(login_url='login')
def membership_payment_delete_global(request, payment_id):
    if _is_secretary(request.user):
        return redirect('membership_payments_list')
    payment = get_object_or_404(Payment, pk=payment_id)
    membership = payment.membership
    payment.delete()
    if membership:
        membership.recalculate_status()
    return redirect('membership_payments_list')


@login_required(login_url='login')
def student_search_api(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 3:
        return JsonResponse({'results': []})
    students = Student.objects.filter(retired=False).filter(
        Q(name__icontains=q) | Q(dni__icontains=q)
    ).order_by('name')[:15]
    results = [
        {
            'id': s.pk,
            'label': f'{s.name}' + (f' — DNI: {s.dni}' if s.dni else ''),
            'name': s.name,
            'dni': s.dni or '',
        }
        for s in students
    ]
    return JsonResponse({'results': results})
