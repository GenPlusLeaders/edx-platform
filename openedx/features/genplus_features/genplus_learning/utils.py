import statistics

from django.conf import settings
from django.apps import apps
from django.test import RequestFactory
from openedx.core.lib.gating.api import get_subsection_completion_percentage
from lms.djangoapps.courseware.courses import get_course_blocks_completion_summary
from openedx.features.course_experience.utils import get_course_outline_block_tree
from xmodule.modulestore.django import modulestore
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


def get_lesson_progress(section_usage_key, user):
    section_block = modulestore().get_item(section_usage_key)
    subsection_blocks = section_block.children
    percentages = [
        get_subsection_completion_percentage(block_usage_key, user)
        for block_usage_key in subsection_blocks
    ]
    return round(statistics.fmean(percentages)) if percentages else 0


def get_unit_progress(course_key, user):
    completion_summary = get_course_blocks_completion_summary(course_key, user)
    if completion_summary:
        total_count = completion_summary['complete_count'] + completion_summary['incomplete_count']
        return round((completion_summary['complete_count'] / total_count) * 100) if total_count else 0


def get_class_lesson_progress(section_usage_key, gen_class):
    percentages = []
    for student in gen_class.students.all():
        percentages.append(get_lesson_progress(section_usage_key, student.gen_user.user))

    return round(statistics.fmean(percentages)) if percentages else 0


def get_class_unit_progress(course_key, gen_class):
    percentages = []
    for student in gen_class.students.all():
        percentages.append(get_unit_progress(course_key, student.gen_user.user))

    return round(statistics.fmean(percentages)) if percentages else 0


def get_course_completion(course_key, user, include_block_children, block_id=None, request=None):
    if request is None:
        request = RequestFactory().get(u'/')
        request.user = user

    course_outline_blocks = get_course_outline_block_tree(
        request, course_key, request.user
    )

    if not course_outline_blocks:
        return None

    completion = get_course_block_completion(
        course_outline_blocks,
        include_block_children,
        block_id
    )

    return completion


def get_course_block_completion(course_block, include_block_children, block_id=None):

    if course_block is None:
        return {
            'block_type': None,
            'total_blocks': 0,
            'total_completed_blocks': 0,
        }

    course_block_children = course_block.get('children')
    block_type = course_block.get('type')
    completion = {
        'id': course_block.get('id'),
        'block_type': block_type,
    }

    if not course_block_children:
        completion['attempted'] = block_id is not None and block_id == course_block.get('block_id')
        if course_block.get('complete'):
            completion['total_blocks'] = 1
            completion['total_completed_blocks'] = 1
        else:
            completion['total_blocks'] = 1
            completion['total_completed_blocks'] = 0
        return completion

    completion['total_blocks'] = 0
    completion['total_completed_blocks'] = 0
    if block_type in include_block_children:
        completion['children'] = []

    attempted = False
    for block in course_block_children:
        child_completion = get_course_block_completion(
            block,
            include_block_children,
            block_id
        )

        completion['total_blocks'] += child_completion['total_blocks']
        completion['total_completed_blocks'] += child_completion['total_completed_blocks']
        attempted = attempted or child_completion['attempted']

        if block_type in include_block_children:
            completion['children'].append(child_completion)

    completion['attempted'] = attempted
    return completion


def get_progress_and_completion_status(total_completed_blocks, total_blocks):
    progress = round((total_completed_blocks / total_blocks) * 100) if total_blocks else 0
    is_complete = total_blocks == total_completed_blocks if total_blocks else False
    return progress, is_complete
