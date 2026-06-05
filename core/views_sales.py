from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SaleForm
from .models import Sale
from .views import _ensure_admin

PAGE_SIZES = (10, 20, 50)


def _per_page(request):
    try:
        size = int(request.GET.get('per_page', 10))
    except (TypeError, ValueError):
        return 10
    return size if size in PAGE_SIZES else 10


def _sales_list_query_params(request, page=None):
    params = {}
    per_page = _per_page(request)
    edit_id = request.GET.get('edit', '').strip()
    if edit_id:
        params['edit'] = edit_id
    if per_page != 10:
        params['per_page'] = str(per_page)
    if page:
        params['page'] = str(page)
    return params


def _paginate(qs, request):
    per_page = _per_page(request)
    page_obj = Paginator(qs, per_page).get_page(request.GET.get('page'))
    return page_obj, per_page


@login_required(login_url='login')
def sales_list(request):
    admin_redirect = _ensure_admin(request)
    if admin_redirect:
        return admin_redirect

    sale_to_edit = None
    edit_id = request.GET.get('edit') or request.POST.get('edit_id')

    if request.method == 'POST':
        if edit_id:
            sale_to_edit = get_object_or_404(Sale, pk=edit_id)
        form = SaleForm(request.POST, instance=sale_to_edit)
        if form.is_valid():
            form.save()
            return redirect('sales_list')
    else:
        if edit_id:
            sale_to_edit = get_object_or_404(Sale, pk=edit_id)
            form = SaleForm(instance=sale_to_edit)
        else:
            form = SaleForm()

    sales_qs = Sale.objects.select_related('shift').order_by('-created_at')
    page_obj, per_page = _paginate(sales_qs, request)
    return render(request, 'core/sales/list.html', {
        'page_obj': page_obj,
        'per_page': per_page,
        'page_sizes': PAGE_SIZES,
        'list_query': urlencode(_sales_list_query_params(request)),
        'form': form,
        'create_mode': sale_to_edit is None,
        'edit_mode': bool(sale_to_edit),
        'sale': sale_to_edit,
    })

@login_required(login_url='login')
def sale_delete(request, sale_id):
    admin_redirect = _ensure_admin(request)
    if admin_redirect:
        return admin_redirect

    sale = get_object_or_404(Sale, pk=sale_id)
    if request.method == 'POST':
        sale.delete()
    return redirect('sales_list')

