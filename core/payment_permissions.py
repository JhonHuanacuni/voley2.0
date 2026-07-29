from django.utils import timezone

from .permissions import is_admin


def payment_can_edit(user, payment):
    return is_admin(user)


def mark_payment_receipt_issued(payment, user):
    if payment.receipt_issued_at:
        return
    payment.receipt_issued_at = timezone.now()
    if user is not None and getattr(user, 'is_authenticated', False):
        payment.receipt_issued_by = user
    payment.save(update_fields=['receipt_issued_at', 'receipt_issued_by', 'updated_at', 'updated_by'])
