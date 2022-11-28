from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.roles import GlobalStaff
from openedx.core.djangolib.js_utils import dump_js_escaped_json

from .utils import update_class_lessons


@login_required
@ensure_csrf_cookie
@require_GET
def update_lessons_structure(request, course_key_string):
    if not GlobalStaff().has_user(request.user):
        raise PermissionDenied()

    content_type = request.META.get('CONTENT_TYPE', None)
    if content_type is None:
        content_type = 'application/json; charset=utf-8'

    try:
        course_key = CourseKey.from_string(course_key_string)
        update_class_lessons(course_key)
    except:
        return HttpResponse(dump_js_escaped_json({
            'user_message': 'An error occurred while updating lessons'
        }), content_type=content_type, status=500)

    return HttpResponse(dump_js_escaped_json({
        'user_message': _('Lessons have been updated')
    }), content_type=content_type, status=200)
