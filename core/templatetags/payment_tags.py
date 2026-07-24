from django import template

from core.payment_permissions import payment_can_edit

register = template.Library()


@register.filter
def payment_editable(payment, user):
    return payment_can_edit(user, payment)
