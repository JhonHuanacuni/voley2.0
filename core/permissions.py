from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def get_user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'admin'
    profile = getattr(user, 'userprofile', None)
    if profile is not None:
        return profile.role
    return 'secretary'


def is_admin(user):
    return get_user_role(user) == 'admin'


def is_secretary(user):
    return get_user_role(user) == 'secretary'


def ensure_admin(request, redirect_to='dashboard'):
    if not is_admin(request.user):
        messages.error(request, 'No tiene permiso para acceder a esta sección.')
        return redirect(redirect_to)
    return None


def ensure_can_modify(request, redirect_to=None):
    """Secretarias solo pueden crear registros, no editarlos ni eliminarlos."""
    if is_secretary(request.user):
        messages.error(request, 'No tiene permiso para modificar o eliminar registros.')
        if redirect_to:
            return redirect(redirect_to)
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect(reverse('dashboard'))
    return None
