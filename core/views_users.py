from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SystemUserCreateForm, SystemUserUpdateForm
from .models import UserProfile
from .views import _ensure_admin, get_user_role


def _users_queryset():
    return User.objects.select_related('userprofile').order_by('username')


def _active_admins_count(exclude_user_id=None):
    qs = UserProfile.objects.filter(role='admin', user__is_active=True)
    if exclude_user_id:
        qs = qs.exclude(user_id=exclude_user_id)
    return qs.count()


@login_required(login_url='login')
def user_list(request):
    admin_redirect = _ensure_admin(request)
    if admin_redirect:
        return admin_redirect

    users = _users_queryset()
    show_create = request.GET.get('create') == '1'
    form = None

    if request.method == 'POST':
        show_create = True
        form = SystemUserCreateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = User.objects.create_user(
                username=data['username'],
                password=data['password'],
                email=data.get('email') or '',
                first_name=data.get('first_name') or '',
                last_name=data.get('last_name') or '',
            )
            user.is_active = data.get('is_active', True)
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = data['role']
            profile.save(update_fields=['role'])
            return redirect('users_list')
    elif show_create:
        form = SystemUserCreateForm()

    return render(request, 'core/users.html', {
        'users': users,
        'form': form,
        'create_mode': show_create,
    })


@login_required(login_url='login')
def user_create(request):
    admin_redirect = _ensure_admin(request)
    if admin_redirect:
        return admin_redirect
    return redirect('users_list')


@login_required(login_url='login')
def user_edit(request, user_id):
    admin_redirect = _ensure_admin(request)
    if admin_redirect:
        return admin_redirect

    user = get_object_or_404(_users_queryset(), pk=user_id)
    form = SystemUserUpdateForm(request.POST or None, instance=user)

    if request.method == 'POST' and form.is_valid():
        role = form.cleaned_data['role']
        is_active = form.cleaned_data.get('is_active', True)
        if not is_active and user.pk == request.user.pk:
            form.add_error('is_active', 'No puede desactivar su propio usuario.')
        elif role != 'admin' and user.pk == request.user.pk and _active_admins_count(exclude_user_id=user.pk) == 0:
            form.add_error('role', 'No puede quitarse el rol de administrador si es el único activo.')
        else:
            user = form.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save(update_fields=['role'])
            new_password = form.cleaned_data.get('password')
            if new_password:
                user.set_password(new_password)
                user.save(update_fields=['password'])
            return redirect('users_list')

    return render(request, 'core/users.html', {
        'users': _users_queryset(),
        'form': form,
        'edit_user': user,
        'edit_mode': True,
    })


@login_required(login_url='login')
def user_delete(request, user_id):
    admin_redirect = _ensure_admin(request)
    if admin_redirect:
        return admin_redirect

    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        if user.pk == request.user.pk:
            return redirect('users_list')
        profile = getattr(user, 'userprofile', None)
        if profile and profile.role == 'admin' and _active_admins_count(exclude_user_id=user.pk) == 0:
            return redirect('users_list')
        user.delete()

    return redirect('users_list')
