from django.dispatch import receiver
from xmodule.modulestore.django import SignalHandler, modulestore

from .models import Unit, Lesson


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):
    course = modulestore().get_course(course_key)
    unit, created = Unit.objects.get_or_create(course_key=course_key)
    latest_sections = set(course.children)

    for section in latest_sections:
        Lesson.objects.get_or_create(unit_id=course_key, usage_key=section)

    sections = set(unit.lessons.values_list('usage_key', flat=True))
    for section in (sections - latest_sections):
        Lesson.objects.get(unit_id=course_key, usage_key=section).delete()
