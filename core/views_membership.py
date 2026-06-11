import json
from datetime import date, timedelta

from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import MembershipForm, MembershipRenewForm, PaymentForm
from .models import Membership, Payment, Shift, Student, active_cycle_choices, valid_cycle_id
from .receipt_pdf import fill_payment_receipt
from .views import get_user_role

_MEMBERSHIP_FILTER_KEYS = ('q', 'cycle', 'shift', 'date_from', 'date_to', 'per_page')
_PAYMENT_FILTER_KEYS = ('membership', 'cycle', 'shift', 'date_from', 'date_to', 'per_page')
PAGE_SIZES = (10, 20, 50)

MONTHS_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
}


def _membership_queryset():
    return Membership.objects.select_related('student', 'student__shift').order_by('-start_date', '-created_at')


def _parse_date_param(value):
    if not value:
        return None
    try:
        parts = value.split('-')
        if len(parts) == 3:
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, TypeError):
        pass
    return None


def _valid_shift_id(value):
    if not value or not str(value).isdigit():
        return ''
    if Shift.objects.filter(pk=int(value)).exists():
        return str(value)
    return ''


def _shift_choices():
    return [(str(shift.id), str(shift)) for shift in Shift.objects.order_by('name')]


def _per_page(request):
    try:
        size = int(request.GET.get('per_page', 10))
    except (TypeError, ValueError):
        return 10
    return size if size in PAGE_SIZES else 10


def _filter_query_params(request, keys):
    params = {key: request.GET.get(key, '').strip() for key in keys if request.GET.get(key, '').strip()}
    per_page = _per_page(request)
    if per_page != 10 and 'per_page' in keys:
        params['per_page'] = str(per_page)
    return params


def _membership_list_query_params(request, page=None):
    params = _filter_query_params(request, _MEMBERSHIP_FILTER_KEYS)
    if page:
        params['page'] = str(page)
    return params


def _payment_list_query_params(request, page=None):
    params = _filter_query_params(request, _PAYMENT_FILTER_KEYS)
    if page:
        params['page'] = str(page)
    return params


def _paginate(qs, request):
    per_page = _per_page(request)
    page_obj = Paginator(qs, per_page).get_page(request.GET.get('page'))
    return page_obj, per_page


def _append_query_params(url, params):
    if not params:
        return url
    separator = '&' if '?' in url else '?'
    return url + separator + '&'.join(f'{key}={value}' for key, value in params.items())


def _apply_membership_list_filters(qs, request):
    query = request.GET.get('q', '').strip()
    cycle_filter = valid_cycle_id(request.GET.get('cycle', ''))
    shift_filter = _valid_shift_id(request.GET.get('shift', ''))
    date_from = _parse_date_param(request.GET.get('date_from', ''))
    date_to = _parse_date_param(request.GET.get('date_to', ''))

    if query:
        qs = qs.filter(
            Q(student__name__icontains=query)
            | Q(student__dni__icontains=query)
        )
    if cycle_filter:
        qs = qs.filter(student__cycle_id=int(cycle_filter))
    if shift_filter:
        qs = qs.filter(student__shift_id=int(shift_filter))
    if date_from:
        qs = qs.filter(end_date__gte=date_from)
    if date_to:
        qs = qs.filter(start_date__lte=date_to)

    return qs, {
        'query': query,
        'cycle_filter': cycle_filter,
        'shift_filter': shift_filter,
        'shift_choices': _shift_choices(),
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
    }


def _apply_payment_list_filters(qs, request):
    membership_filter = request.GET.get('membership', '').strip()
    cycle_filter = valid_cycle_id(request.GET.get('cycle', ''))
    shift_filter = _valid_shift_id(request.GET.get('shift', ''))
    date_from = _parse_date_param(request.GET.get('date_from', ''))
    date_to = _parse_date_param(request.GET.get('date_to', ''))

    if membership_filter.isdigit():
        qs = qs.filter(membership_id=int(membership_filter))
    if cycle_filter:
        qs = qs.filter(student__cycle_id=int(cycle_filter))
    if shift_filter:
        qs = qs.filter(student__shift_id=int(shift_filter))
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)

    return qs, {
        'selected_membership': membership_filter if membership_filter.isdigit() else '',
        'cycle_filter': cycle_filter,
        'shift_filter': shift_filter,
        'shift_choices': _shift_choices(),
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
    }


def _membership_list_filter_defaults():
    return {
        'cycle_choices': active_cycle_choices(),
        'shift_choices': _shift_choices(),
        'query': '',
        'cycle_filter': '',
        'shift_filter': '',
        'date_from': '',
        'date_to': '',
        'per_page': 10,
        'page_sizes': PAGE_SIZES,
        'list_query': '',
    }


def _payment_list_filter_defaults():
    return {
        'cycle_choices': active_cycle_choices(),
        'shift_choices': _shift_choices(),
        'selected_membership': '',
        'cycle_filter': '',
        'shift_filter': '',
        'date_from': '',
        'date_to': '',
        'per_page': 10,
        'page_sizes': PAGE_SIZES,
        'list_query': '',
    }


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
    memberships, filter_ctx = _apply_membership_list_filters(_membership_queryset(), request)
    page_obj, per_page = _paginate(memberships, request)

    return render(request, 'core/memberships/list.html', {
        'page_obj': page_obj,
        'per_page': per_page,
        'page_sizes': PAGE_SIZES,
        'list_query': urlencode(_membership_list_query_params(request)),
        'cycle_choices': active_cycle_choices(),
        'is_secretary': _is_secretary(request.user),
        **filter_ctx,
    })


@login_required(login_url='login')
def membership_create(request):
    form = MembershipForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        membership = form.save()
        Membership.sync_student_dates(membership.student)
        return redirect('memberships_list')
    page_obj, per_page = _paginate(_membership_queryset(), request)
    return render(request, 'core/memberships/list.html', {
        'page_obj': page_obj,
        'per_page': per_page,
        'form': form,
        'create_mode': True,
        'is_secretary': _is_secretary(request.user),
        **_membership_list_filter_defaults(),
    })


@login_required(login_url='login')
def membership_edit(request, membership_id):
    membership = get_object_or_404(Membership, pk=membership_id)
    form = MembershipForm(request.POST or None, instance=membership)
    if request.method == 'POST' and form.is_valid():
        membership = form.save()
        membership.recalculate_status()
        Membership.sync_student_dates(membership.student)
        return redirect('memberships_list')
    page_obj, per_page = _paginate(_membership_queryset(), request)
    return render(request, 'core/memberships/list.html', {
        'page_obj': page_obj,
        'per_page': per_page,
        'form': form,
        'membership': membership,
        'edit_mode': True,
        'is_secretary': _is_secretary(request.user),
        **_membership_list_filter_defaults(),
    })


@login_required(login_url='login')
def membership_delete(request, membership_id):
    if _is_secretary(request.user):
        return redirect('memberships_list')
    membership = get_object_or_404(Membership, pk=membership_id)
    student = membership.student
    membership.delete()
    Membership.sync_student_dates(student)
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
        payment_amount = form.cleaned_data.get('payment_amount')
        if payment_amount and payment_amount > 0:
            Payment.objects.create(
                membership=renewed,
                student=old.student,
                date=timezone.localdate(),
                amount=payment_amount,
                method=form.cleaned_data.get('payment_method') or 'efectivo',
            )
        else:
            renewed.recalculate_status()
        Membership.sync_student_dates(old.student)
        return redirect('memberships_list')
    return render(request, 'core/memberships/renew.html', {
        'form': form,
        'membership': old,
        'payment_date': timezone.localdate(),
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
    payments_qs = Payment.objects.select_related('membership', 'student').order_by('-date')
    page_obj, per_page = _paginate(payments_qs, request)
    return render(request, 'core/memberships/payments_list.html', {
        'page_obj': page_obj,
        'per_page': per_page,
        'memberships': _membership_queryset(),
        'form': form,
        'create_mode': True,
        'is_secretary': _is_secretary(request.user),
        **_payment_list_filter_defaults(),
    })


@login_required(login_url='login')
def membership_payments_list(request):
    payments_qs = Payment.objects.select_related(
        'membership', 'membership__student', 'student', 'student__shift',
    ).order_by('-date')
    payments, filter_ctx = _apply_payment_list_filters(payments_qs, request)
    memberships = _membership_queryset()

    form = PaymentForm(
        request.POST or None,
        membership_qs=_membership_queryset(),
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        url = _append_query_params(
            reverse('membership_payments_list'),
            _filter_query_params(request, _PAYMENT_FILTER_KEYS),
        )
        return redirect(url)

    page_obj, per_page = _paginate(payments, request)
    return render(request, 'core/memberships/payments_list.html', {
        'page_obj': page_obj,
        'per_page': per_page,
        'page_sizes': PAGE_SIZES,
        'list_query': urlencode(_payment_list_query_params(request)),
        'memberships': memberships,
        'form': form,
        'cycle_choices': active_cycle_choices(),
        'create_mode': False,
        'is_secretary': _is_secretary(request.user),
        **filter_ctx,
    })


@login_required(login_url='login')
def membership_payment_edit(request, payment_id):
    payment = get_object_or_404(Payment.objects.select_related('membership'), pk=payment_id)
    list_params = _filter_query_params(request, _PAYMENT_FILTER_KEYS)
    if not list_params.get('membership') and payment.membership_id:
        list_params['membership'] = str(payment.membership_id)
    form = PaymentForm(
        request.POST or None,
        instance=payment,
        membership_qs=_membership_queryset(),
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        if payment.membership_id:
            return redirect('membership_payments', membership_id=payment.membership_id)
        return redirect(_append_query_params(reverse('membership_payments_list'), list_params))

    payments_qs = Payment.objects.select_related('membership', 'student').order_by('-date')
    payments, filter_ctx = _apply_payment_list_filters(payments_qs, request)

    page_obj, per_page = _paginate(payments, request)
    return render(request, 'core/memberships/payments_list.html', {
        'page_obj': page_obj,
        'per_page': per_page,
        'page_sizes': PAGE_SIZES,
        'list_query': urlencode(_payment_list_query_params(request)),
        'memberships': _membership_queryset(),
        'form': form,
        'payment': payment,
        'edit_mode': True,
        'cycle_choices': active_cycle_choices(),
        'is_secretary': _is_secretary(request.user),
        **filter_ctx,
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
