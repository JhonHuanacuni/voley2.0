from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .financial_report_export import build_financial_report_workbook, compute_financial_summary
from .views import _ensure_admin, get_user_role


@login_required(login_url='login')
def financial_report_view(request):
    admin_redirect = _ensure_admin(request)
    if admin_redirect:
        return admin_redirect

    today = date.today()
    try:
        report_year = int(request.GET.get('year', today.year))
    except (TypeError, ValueError):
        report_year = today.year
    try:
        report_month = int(request.GET.get('month', today.month))
    except (TypeError, ValueError):
        report_month = today.month
    if report_month < 1 or report_month > 12:
        report_month = today.month

    summary = compute_financial_summary(report_year, report_month)
    return render(request, 'core/financial_report.html', {
        'report_year': report_year,
        'report_month': report_month,
        'summary': summary,
        'user_role': get_user_role(request.user),
        'is_admin': get_user_role(request.user) == 'admin',
    })


@login_required(login_url='login')
def export_financial_report_xlsx(request):
    admin_redirect = _ensure_admin(request)
    if admin_redirect:
        return admin_redirect

    today = date.today()
    try:
        year = int(request.GET.get('year', today.year))
    except (TypeError, ValueError):
        year = today.year
    try:
        month = int(request.GET.get('month', today.month))
    except (TypeError, ValueError):
        month = today.month
    if month < 1 or month > 12:
        month = today.month

    wb, data = build_financial_report_workbook(year, month)
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = (
        f'attachment; filename=vita_voley_reporte_financiero_{year}_{month:02d}.xlsx'
    )
    wb.save(response)
    return response
