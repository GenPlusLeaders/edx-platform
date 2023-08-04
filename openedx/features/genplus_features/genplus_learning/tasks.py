import logging
from datetime import datetime
import pytz

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import UsageKey, CourseKey
from completion.models import BlockCompletion
from completion.waffle import ENABLE_COMPLETION_TRACKING_SWITCH
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.course_modes.models import CourseMode
from openedx.features.genplus_features.genplus.models import Class, Student
from openedx.features.genplus_features.genplus.constants import GenUserRoles
from openedx.features.genplus_features.genplus_learning.models import (
    Program, ProgramEnrollment, UnitCompletion, UnitBlockCompletion
)
from openedx.features.genplus_features.genplus_learning.constants import ProgramEnrollmentStatuses
from openedx.features.genplus_features.genplus_learning.utils import (
    get_course_completion,
    get_progress_and_completion_status
)
from openedx.features.genplus_features.genplus_learning.access import allow_access, revoke_access
from openedx.features.genplus_features.genplus_learning.roles import ProgramStaffRole

log = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def enroll_class_students_to_program(self, class_id, program_id, class_student_ids=[], program_unit_ids=[]):
    try:
        gen_class = Class.objects.get(pk=class_id)
        program = Program.objects.get(pk=program_id)
    except ObjectDoesNotExist:
        log.info("Class or program id does not exist")
        return

    units = program.units.all()
    all_students = gen_class.students.select_related('gen_user').all()
    # if students are already the part of same program with different class then delete those enrollments
    ProgramEnrollment.objects \
        .filter(program=program, student__in=all_students) \
        .exclude(gen_class=gen_class) \
        .delete()
    enrolled_students = ProgramEnrollment.objects \
        .filter(program=program, gen_class=gen_class, student__in=all_students) \
        .values_list('student', flat=True)
    unenrolled_students = all_students.exclude(pk__in=enrolled_students)

    if program_unit_ids:
        units = units.filter(program__in=program_unit_ids)

    if class_student_ids:
        unenrolled_students = unenrolled_students.filter(pk__in=class_student_ids)

    if not unenrolled_students:
        return

    program_enrollments = [
        ProgramEnrollment(
            student=student,
            program=program,
            gen_class=gen_class,
            status=ProgramEnrollmentStatuses.PENDING
        )
        for student in unenrolled_students
    ]
    ProgramEnrollment.objects.bulk_create(program_enrollments)

    unit_ids = units.values_list('course', flat=True)
    courses = []
    if program.intro_unit:
        courses.append(program.intro_unit)

    if program.outro_unit:
        courses.append(program.outro_unit)

    courses += [unit.course for unit in units]

    for student in unenrolled_students:
        if student.gen_user.user:
            for course in courses:
                course_enrollment, created = CourseEnrollment.objects.get_or_create(
                    user=student.gen_user.user, course=course, mode=CourseMode.AUDIT
                )
            student.active_class = gen_class
            student.save()
            ProgramEnrollment.objects.filter(program=program, student=student).update(status=ProgramEnrollmentStatuses.ENROLLED)
            log.info("Program and Unit Enrollments successfully created for student: %s", student)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def unenroll_class_students_from_program(self, class_id, program_id, class_student_ids=[]):
    try:
        gen_class = Class.objects.get(pk=class_id)
        program = Program.objects.get(pk=program_id)
    except ObjectDoesNotExist:
        log.info("Class or program id does not exist")
        return

    removed_class_students = Student.objects.filter(pk__in=class_student_ids)

    for student in removed_class_students:
        ProgramEnrollment.objects.filter(program=program, gen_class=gen_class, student=student).delete()
        if student.active_class.pk == gen_class.pk:
            student.active_class = None
            student.save()


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def allow_program_access_to_class_teachers(self, class_id, program_id, class_teacher_ids=[]):
    try:
        gen_class = Class.objects.get(pk=class_id)
        program = Program.objects.get(pk=program_id)
    except ObjectDoesNotExist:
        log.info("Class or program id does not exist")
        return

    users = User.objects.filter(gen_user__school=gen_class.school, gen_user__role__in=GenUserRoles.TEACHING_ROLES)
    if class_teacher_ids:
        users = users.filter(gen_user__teacher__in=class_teacher_ids)

    allow_access(program, ProgramStaffRole.ROLE_NAME, users)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def revoke_program_access_for_class_teachers(self, class_id, program_id, class_teacher_ids=[]):
    try:
        gen_class = Class.objects.get(pk=class_id)
        program = Program.objects.get(pk=program_id)
    except ObjectDoesNotExist:
        log.info("Class or program id does not exist")
        return

    users = User.objects.filter(gen_user__school=gen_class.school, gen_user__role__in=GenUserRoles.TEACHING_ROLES)
    if class_teacher_ids:
        users = users.filter(gen_user__teacher__in=class_teacher_ids)

    revoke_access(program, ProgramStaffRole.ROLE_NAME, users)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def update_unit_and_lesson_completions(self, user_id, course_key_str, usage_key_str):
    if not ENABLE_COMPLETION_TRACKING_SWITCH.is_enabled():
        return

    usage_key = UsageKey.from_string(usage_key_str)
    block_type = usage_key.block_type
    aggregator_types = ['course', 'chapter', 'sequential', 'vertical']

    if block_type not in aggregator_types:
        course_key = CourseKey.from_string(course_key_str)
        block_id = usage_key.block_id
        user = User.objects.get(id=user_id)
        course_completion = get_course_completion(course_key_str, user, ['course'], block_id)

        if not (course_completion and course_completion.get('attempted')):
            return

        progress, is_complete = get_progress_and_completion_status(
            course_completion.get('total_completed_blocks'),
            course_completion.get('total_blocks')
        )
        defaults = {
            'progress': progress,
            'is_complete': is_complete,
        }
        if is_complete:
            defaults['completion_date'] = datetime.now().replace(tzinfo=pytz.UTC)

        UnitCompletion.objects.update_or_create(
            user=user, course_key=course_key,
            defaults=defaults
        )

        for block in course_completion['children']:
            if block['attempted']:
                progress, is_complete = get_progress_and_completion_status(
                    block.get('total_completed_blocks'),
                    block.get('total_blocks')
                )
                block_usage_key = UsageKey.from_string(block['id'])
                defaults = {
                    'progress': progress,
                    'is_complete': is_complete,
                    'block_type': block.get('block_type'),
                }
                if is_complete:
                    defaults['completion_date'] = datetime.now().replace(tzinfo=pytz.UTC)
                    BlockCompletion.objects.submit_completion(
                        user=user,
                        block_key=block_usage_key,
                        completion=1.0,
                    )

                UnitBlockCompletion.objects.update_or_create(
                    user=user, course_key=course_key, usage_key=block_usage_key,
                    defaults=defaults
                )

                return
