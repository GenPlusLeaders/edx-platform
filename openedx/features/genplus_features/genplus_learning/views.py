from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from opaque_keys.edx.keys import CourseKey
from rest_framework.exceptions import NotFound, PermissionDenied

from common.djangoapps.student.roles import GlobalStaff
from completion_aggregator.api.v1.views import CompletionDetailView
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
        content_type = "application/json; charset=utf-8"

    try:
        course_key = CourseKey.from_string(course_key_string)
        update_class_lessons(course_key)
    except:
        return HttpResponse(dump_js_escaped_json({
            "user_message": "An error occurred while updating lessons"
        }), content_type=content_type, status=500)

    return HttpResponse(dump_js_escaped_json({
        "user_message": _("Lessons have been updated")
    }), content_type=content_type, status=200)


class GenPlusCompletionDetailView(CompletionDetailView):
    @property
    def user(self):
        """
        Return the effective user.

        Usually the requesting user, but a staff user can override this.
        """
        if self._effective_user:
            return self._effective_user

        if self.request.method == "GET":
            requested_username = self.request.GET.get('username')
        else:
            requested_username = self.request.data.get('username')

        if not requested_username:
            if self.request.user.is_staff:
                user = self.request.user
                self._requested_user = None
            else:
                raise PermissionDenied()
        else:
            if self.request.user.is_staff or self.request.user.gen_user.is_teacher:
                try:
                    user = User.objects.get(username=requested_username)
                except User.DoesNotExist as exc:
                    raise NotFound() from exc
            else:
                if self.request.user.username.lower() == requested_username.lower():
                    user = self.request.user
                else:
                    raise PermissionDenied()
            self._requested_user = user
        self._effective_user = user
        return self._effective_user
