# lint-amnesty, pylint: disable=missing-module-docstring
import functools

from django.db import transaction
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError

from common.djangoapps.edxmako.shortcuts import render_to_response, render_to_string
from common.djangoapps.util.views import fix_crum_request
from openedx.core.djangolib.js_utils import dump_js_escaped_json
from openedx.features.genplus_features.genplus.models import GenError, GenUser

__all__ = ['not_found', 'server_error', 'render_404', 'render_500']


def jsonable_error(status=500, message="The Studio servers encountered an error"):
    """
    A decorator to make an error view return an JSON-formatted message if
    it was requested via AJAX.
    """
    def outer(func):
        @functools.wraps(func)
        def inner(request, *args, **kwargs):
            if request.is_ajax():
                content = dump_js_escaped_json({"error": message})
                return HttpResponse(content, content_type="application/json",  # lint-amnesty, pylint: disable=http-response-with-content-type-json
                                    status=status)
            else:
                return func(request, *args, **kwargs)
        return inner
    return outer


@jsonable_error(404, "Resource not found")
def not_found(request, exception):  # lint-amnesty, pylint: disable=unused-argument
    return render_to_response('error.html', {'error': '404'})


@jsonable_error(500, "The Studio servers encountered an error")
def server_error(request):
    return render_to_response('error.html', {'error': '500'})


@fix_crum_request
@jsonable_error(404, "Resource not found")
def render_404(request, exception):  # lint-amnesty, pylint: disable=unused-argument
    return HttpResponseNotFound(render_to_string('404.html', {}, request=request))


@fix_crum_request
@jsonable_error(500, "The Studio servers encountered an error")
def render_500(request):
    try:
        with transaction.atomic():
            gen_user = GenUser.objects.filter(user=request.user).first()
            profile_name = request.user.profile.name if request.user.profile else ''
            gen_error = GenError.objects.create(
                email=request.user.email,
                name=profile_name,
                error_code=500,
                device=request.user_agent.device.family,
                os=f'{request.user_agent.os.family}-{request.user_agent.os.version_string}',
                browser=f'{request.user_agent.browser.family}-{request.user_agent.browser.version_string}'
            )
            if gen_user:
                gen_error.role = gen_user.role
                gen_error.school = gen_user.school
                if gen_user.is_student:
                    gen_error.gen_class = gen_user.student.active_class

                gen_error.save()
    except:
        pass

    return HttpResponseServerError(render_to_string('500.html', {}, request=request))
