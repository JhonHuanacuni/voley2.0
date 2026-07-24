import threading
from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils import timezone

_thread_locals = threading.local()

# Campos de auditoría que no deben aparecer en el detalle de cambios.
AUDIT_META_FIELDS = frozenset({
    'updated_at',
    'updated_by',
    'updated_by_id',
    'created_by',
    'created_by_id',
})

# Modelos importantes auditados (app_label.ModelName).
AUDITED_MODEL_LABELS = frozenset({
    'core.Student',
    'core.Membership',
    'core.Payment',
    'core.Sale',
    'core.Expense',
    'core.Attendance',
    'core.Shift',
    'core.Cycle',
    'core.UserProfile',
})


def set_current_user(user):
    _thread_locals.user = user


def get_current_user():
    return getattr(_thread_locals, 'user', None)


class AuditMiddleware:
    """Guarda el usuario autenticado de la petición para usarlo en señales."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, 'user', None) and request.user.is_authenticated:
            set_current_user(request.user)
        else:
            set_current_user(None)
        try:
            return self.get_response(request)
        finally:
            set_current_user(None)


def _serialize_value(value):
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (list, dict, tuple)):
        return value
    if hasattr(value, 'pk'):
        return value.pk
    return value


def _instance_snapshot(instance):
    data = model_to_dict(instance)
    snapshot = {}
    for field_name, value in data.items():
        if field_name in AUDIT_META_FIELDS:
            continue
        snapshot[field_name] = _serialize_value(value)
    return snapshot


def _build_changes(old_instance, new_instance):
    if old_instance is None:
        return {
            field_name: {'old': None, 'new': value}
            for field_name, value in _instance_snapshot(new_instance).items()
        }

    old_data = _instance_snapshot(old_instance)
    new_data = _instance_snapshot(new_instance)
    changes = {}
    for field_name in sorted(set(old_data) | set(new_data)):
        old_value = old_data.get(field_name)
        new_value = new_data.get(field_name)
        if old_value != new_value:
            changes[field_name] = {'old': old_value, 'new': new_value}
    return changes


def _write_audit_log(action, instance, changes):
    from .models import AuditLog

    user = get_current_user()
    if user is not None and not getattr(user, 'is_authenticated', False):
        user = None

    AuditLog.objects.create(
        action=action,
        model_name=f'{instance._meta.app_label}.{instance.__class__.__name__}',
        object_id=str(instance.pk),
        object_repr=str(instance)[:255],
        user=user,
        changes=changes or {},
    )


def _is_audited(sender):
    label = f'{sender._meta.app_label}.{sender.__name__}'
    return label in AUDITED_MODEL_LABELS


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    if not _is_audited(sender):
        return

    user = get_current_user()
    if user is not None and getattr(user, 'is_authenticated', False):
        if instance.pk is None:
            instance.created_by = user
        instance.updated_by = user

    if instance.pk:
        try:
            instance._audit_old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._audit_old_instance = None
    else:
        instance._audit_old_instance = None


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    if not _is_audited(sender):
        return

    from .models import AuditLog

    old_instance = getattr(instance, '_audit_old_instance', None)
    if created:
        changes = _build_changes(None, instance)
        action = AuditLog.ACTION_CREATE
    else:
        changes = _build_changes(old_instance, instance)
        if not changes:
            return
        action = AuditLog.ACTION_UPDATE

    _write_audit_log(action, instance, changes)


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    if not _is_audited(sender):
        return

    from .models import AuditLog

    changes = {
        field_name: {'old': value, 'new': None}
        for field_name, value in _instance_snapshot(instance).items()
    }
    _write_audit_log(AuditLog.ACTION_DELETE, instance, changes)


def connect_audit_signals():
    """Importado desde apps.py para registrar señales al iniciar Django."""
    return None
