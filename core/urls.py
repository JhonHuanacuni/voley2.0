from django.urls import path
from django.views.generic import RedirectView
from . import views
from . import views_membership
from . import views_users
from . import views_expenses
from . import views_cycles
from . import views_sales

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard_view, name='dashboard'),
    path('students/', views.student_list, name='students_list'),
    path('students/add/', views.student_create, name='student_add'),
    path('students/<int:student_id>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:student_id>/delete/', views.student_delete, name='student_delete'),
    path('students/<int:student_id>/retire/', views.student_retire, name='student_retire'),
    path('students/<int:student_id>/reactivate/', views.student_reactivate, name='student_reactivate'),
    path('students/retired/', views.retired_list, name='retired_list'),
    path('attendance/', views.attendance_view, name='attendance'),
    path('attendance/qr/', views.attendance_qr_view, name='attendance_qr'),
    path('attendance/<int:attendance_id>/delete/', views.delete_attendance_record, name='attendance_delete'),
    path('students/<int:student_id>/qr/', views.student_qr_view, name='student_qr'),
    # Módulo Membresías
    path('memberships/', views_membership.membership_list, name='memberships_list'),
    path('memberships/add/', views_membership.membership_create, name='membership_add'),
    path('memberships/search/', views_membership.student_search_api, name='membership_student_search'),
    path('memberships/<int:membership_id>/edit/', views_membership.membership_edit, name='membership_edit'),
    path('memberships/<int:membership_id>/delete/', views_membership.membership_delete, name='membership_delete'),
    path('memberships/<int:membership_id>/renew/', views_membership.membership_renew, name='membership_renew'),
    path('memberships/<int:membership_id>/payments/', views_membership.membership_payments, name='membership_payments'),
    path(
        'memberships/<int:membership_id>/payments/<int:payment_id>/delete/',
        views_membership.membership_payment_delete,
        name='membership_payment_delete',
    ),
    path(
        'memberships/<int:membership_id>/payments/<int:payment_id>/receipt/',
        views_membership.membership_payment_receipt,
        name='membership_payment_receipt',
    ),
    # Submódulo Pagos (dentro de membresías)
    path('memberships/payments/', views_membership.membership_payments_list, name='membership_payments_list'),
    path('memberships/payments/add/', views_membership.membership_payment_add, name='membership_payment_add'),
    path('memberships/payments/<int:payment_id>/edit/', views_membership.membership_payment_edit, name='membership_payment_edit'),
    path(
        'memberships/payments/<int:payment_id>/delete/',
        views_membership.membership_payment_delete_global,
        name='membership_payment_delete_global',
    ),
    # Redirecciones URLs antiguas de pagos
    path('payments/', RedirectView.as_view(pattern_name='membership_payments_list', permanent=False), name='payments'),
    path('payments/add/', RedirectView.as_view(pattern_name='membership_payment_add', permanent=False), name='payment_add'),
    path('payments/<int:payment_id>/edit/', views.payment_edit_redirect, name='payment_edit'),
    path('payments/<int:payment_id>/delete/', views.payment_delete_redirect, name='payment_delete'),
    path('payments/<int:payment_id>/receipt/', views.payment_receipt, name='payment_receipt'),
    path('cycles/', views_cycles.cycles_list, name='cycles_list'),
    path('cycles/<int:cycle_id>/edit/', views_cycles.cycle_edit, name='cycle_edit'),
    path('cycles/<int:cycle_id>/delete/', views_cycles.cycle_delete, name='cycle_delete'),
    path('shifts/', views.shifts_list, name='shifts_list'),
    path('shifts/add/', views.shift_create, name='shift_add'),
    path('shifts/<int:shift_id>/edit/', views.shift_edit, name='shift_edit'),
    path('shifts/<int:shift_id>/delete/', views.shift_delete, name='shift_delete'),
    path('users/', views_users.user_list, name='users_list'),
    path('users/add/', views_users.user_create, name='user_add'),
    path('users/<int:user_id>/edit/', views_users.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views_users.user_delete, name='user_delete'),
    path('expenses/', views_expenses.expense_list, name='expenses_list'),
    path('expenses/add/', views_expenses.expense_create, name='expense_add'),
    path('expenses/<int:expense_id>/edit/', views_expenses.expense_edit, name='expense_edit'),
    path('expenses/<int:expense_id>/delete/', views_expenses.expense_delete, name='expense_delete'),
    # Módulo Ventas (solo admin)
    path('sales/', views_sales.sales_list, name='sales_list'),
    path('sales/<int:sale_id>/delete/', views_sales.sale_delete, name='sale_delete'),
    path('reports/', views.report_view, name='reports'),
    path('reports/export/students/', views.export_students_xlsx, name='export_students_xlsx'),
    path('reports/export/attendance/', views.export_attendance_xlsx, name='export_attendance_xlsx'),
    path('reports/export/enrollments/', views.export_monthly_enrollments_xlsx, name='export_monthly_enrollments_xlsx'),
    path('reports/export/payments/', views.export_payments_xlsx, name='export_payments_xlsx'),
]
