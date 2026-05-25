from .models import UserProfile


def user_role_context(request):
    user_role = None
    is_admin = False
    is_secretary = False

    if request.user.is_authenticated:
        if request.user.is_superuser:
            user_role = 'admin'
            is_admin = True
        else:
            profile = getattr(request.user, 'userprofile', None)
            if profile is not None:
                user_role = profile.role
                is_admin = profile.role == 'admin'
                is_secretary = profile.role == 'secretary'
            else:
                user_role = 'secretary'
                is_secretary = True

    return {
        'user_role': user_role,
        'is_admin': is_admin,
        'is_secretary': is_secretary,
    }
