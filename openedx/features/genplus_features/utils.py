from django.contrib.auth.decorators import user_passes_test
from django.http import Http404


def get_full_name(user, default=''):
    if user:
        return user.gen_user.name or default
    return default



def genplus_superuser_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404("Page not found.")
        return view_func(request, *args, **kwargs)
    return wrapper
