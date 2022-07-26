import statistics

from django.conf import settings
from django.apps import apps
from openedx.core.lib.gating.api import get_subsection_completion_percentage
from openedx.features.course_experience.utils import get_course_outline_block_tree
from xmodule.modulestore.django import modulestore

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


def get_section_progress(section_usage_key, user):
    section_block = modulestore().get_item(section_usage_key)
    subsection_blocks = section_block.children
    percentages = [
        get_subsection_completion_percentage(block_usage_key, user)
        for block_usage_key in subsection_blocks
    ]
    return round(statistics.fmean(percentages)) if percentages else 0


def get_course_progress(course_key, user):
    completion_summary = get_course_blocks_completion_summary(course_key, user)
    if completion_summary:
        total_count = completion_summary.complete_count + completion_summary.incomplete_count
        return round((completion_summary.complete_count / total_count) * 100)


def get_class_section_progress(section_usage_key, gen_class):
    percentages = []
    for student in gen_class.students.all():
        percentages.append(get_section_progress(section_usage_key, student.gen_user.user))

    return round(statistics.fmean(percentages)) if percentages else 0


def get_class_course_progress(course_key, gen_class):
    percentages = []
    for student in gen_class.students.all():
        percentages.append(get_course_progress(course_key, student.gen_user.user))

    return round(statistics.fmean(percentages)) if percentages else 0


def get_lms_link_for_unit(unit: CourseOverview):
    course = modulestore().get_course(unit.id)
    course_key_str = str(unit.id)
    sections = course.children
    if sections:
        usage_key_str = str(sections[0])
    else:
        usage_key_str = str(modulestore().make_course_usage_key(unit.id))

    return f"{settings.LMS_ROOT_URL}/courses/{course_key_str}/jump_to/{usage_key_str}"


def get_unit_image_url(unit: CourseOverview):
    return f"{settings.LMS_ROOT_URL}{unit.course_image_url}"


def is_unit_locked(unit: CourseOverview):
    Lesson = apps.get_model('genplus_learning', 'Lesson')

    lessons = Lesson.objects.filter(course_key=unit.id)
    if lessons:
        return all([lesson.is_locked for lesson in lessons])

    return False


def get_user_unit_progress(unit: CourseOverview, user):
    Lesson = apps.get_model('genplus_learning', 'Lesson')

    lessons = Lesson.objects.filter(course_key=unit.id)
    percentages = [lesson.get_user_progress(user) for lesson in lessons.all()]
    return round(statistics.fmean(percentages)) if percentages else 0
