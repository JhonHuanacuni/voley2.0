from .permissions import get_user_role, is_admin, is_secretary


def user_role_context(request):
    user_role = None
    is_admin_user = False
    is_secretary_user = False

    if request.user.is_authenticated:
        user_role = get_user_role(request.user)
        is_admin_user = is_admin(request.user)
        is_secretary_user = is_secretary(request.user)

    return {
        'user_role': user_role,
        'is_admin': is_admin_user,
        'is_secretary': is_secretary_user,
    }
