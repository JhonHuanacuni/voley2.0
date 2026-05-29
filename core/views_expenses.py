from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import ExpenseForm
from .models import Expense
from .views import _ensure_admin


def _expenses_queryset(query=''):
    qs = Expense.objects.all()
    if query:
        qs = qs.filter(
            Q(concept__icontains=query)
            | Q(provider__icontains=query)
            | Q(observations__icontains=query)
        )
    return qs.order_by('-date', '-created_at')


@login_required(login_url='login')
def expense_list(request):
    admin_redirect = _ensure_admin(request)
    if admin_redirect:
        return admin_redirect

    query = request.GET.get('q', '').strip()
    expenses = _expenses_queryset(query)
    show_create = request.GET.get('create') == '1'
    form = None

    if request.method == 'POST':
        show_create = True
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('expenses_list')
    elif show_create:
        form = ExpenseForm()

    return render(request, 'core/expenses.html', {
        'expenses': expenses,
        'query': query,
        'form': form,
        'create_mode': show_create,
    })


@login_required(login_url='login')
def expense_create(request):
    admin_redirect = _ensure_admin(request)
    if admin_redirect:
        return admin_redirect
    return redirect(f"{reverse('expenses_list')}?create=1")


@login_required(login_url='login')
def expense_edit(request, expense_id):
    admin_redirect = _ensure_admin(request)
    if admin_redirect:
        return admin_redirect

    expense = get_object_or_404(Expense, pk=expense_id)
    form = ExpenseForm(request.POST or None, instance=expense)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('expenses_list')

    return render(request, 'core/expenses.html', {
        'expenses': _expenses_queryset(),
        'query': '',
        'form': form,
        'edit_expense': expense,
        'edit_mode': True,
    })


@login_required(login_url='login')
def expense_delete(request, expense_id):
    admin_redirect = _ensure_admin(request)
    if admin_redirect:
        return admin_redirect

    expense = get_object_or_404(Expense, pk=expense_id)
    if request.method == 'POST':
        expense.delete()
    return redirect('expenses_list')
