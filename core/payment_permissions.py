from django.utils import timezone


def is_payment_admin(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True
    from .views import get_user_role
    return get_user_role(user) == 'admin'


def payment_can_edit(user, payment):
    if is_payment_admin(user):
        return True
    return not payment.receipt_issued_at


def mark_payment_receipt_issued(payment, user):
    if payment.receipt_issued_at:
        return
    payment.receipt_issued_at = timezone.now()
    if user is not None and getattr(user, 'is_authenticated', False):
        payment.receipt_issued_by = user
    payment.save(update_fields=['receipt_issued_at', 'receipt_issued_by', 'updated_at', 'updated_by'])
