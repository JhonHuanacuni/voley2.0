from datetime import date, timedelta

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Membership, Payment, Student


def _default_membership_end(start):
    if start.month == 12:
        return start.replace(year=start.year + 1, month=1, day=start.day)
    try:
        return start.replace(month=start.month + 1)
    except ValueError:
        return start + timedelta(days=30)


@receiver(post_save, sender=Student)
def sync_membership_for_student(sender, instance, created, **kwargs):
    start = instance.membership_start or instance.enrollment_date or date.today()
    end = instance.membership_end or _default_membership_end(start)
    amount_due = instance.monthly_fee or 0

    if created:
        Membership.objects.create(
            student=instance,
            start_date=start,
            end_date=end,
            amount_due=amount_due,
            status='completed' if amount_due <= 0 else 'debt',
        )
        Student.objects.filter(pk=instance.pk).update(
            membership_start=start,
            membership_end=end,
        )
        return

    membership = instance.memberships.order_by('-end_date', '-created_at').first()
    if membership:
        membership.start_date = instance.membership_start or membership.start_date
        membership.end_date = instance.membership_end or membership.end_date
        if instance.monthly_fee is not None:
            membership.amount_due = instance.monthly_fee
        membership.save()
        membership.recalculate_status()
    elif instance.membership_start or instance.membership_end:
        Membership.objects.create(
            student=instance,
            start_date=start,
            end_date=end,
            amount_due=amount_due,
            status='completed' if amount_due <= 0 else 'debt',
        )


@receiver(post_delete, sender=Payment)
def update_membership_after_payment_delete(sender, instance, **kwargs):
    membership_id = instance.membership_id
    if membership_id:
        try:
            Membership.objects.get(pk=membership_id).recalculate_status()
        except Membership.DoesNotExist:
            pass
