import logging
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed, pre_save, pre_delete

from completion.models import BlockCompletion
from common.djangoapps.student.models import CourseEnrollment
from xmodule.modulestore.django import SignalHandler, modulestore
from lms.djangoapps.grades.signals.signals import PROBLEM_RAW_SCORE_CHANGED
from openedx.features.genplus_features.genplus.models import Class, Teacher, Activity, GenLog
from openedx.features.genplus_features.genplus.constants import ActivityTypes, GenLogTypes
from openedx.features.genplus_features.genplus_learning.constants import ProgramEnrollmentStatuses
import openedx.features.genplus_features.genplus_learning.tasks as genplus_learning_tasks
from openedx.features.genplus_features.genplus_learning.models import (
    Program, ProgramEnrollment, Unit, ClassUnit, ClassLesson , UnitBlockCompletion
)
from openedx.features.genplus_features.genplus_learning.cache import ProgramCache

log = logging.getLogger(__name__)


def _create_class_unit_and_lessons(gen_class):
    # create class_units and class_lessons for units in this program
    units = gen_class.program.units.all()
    class_lessons = []
    for unit in units:
        class_unit, created = ClassUnit.objects.get_or_create(gen_class=gen_class, unit=unit, course_key=unit.course.id)
        course = modulestore().get_course(class_unit.course_key)
        lessons = course.children
        class_lessons += [
            ClassLesson(order=order, class_unit=class_unit,
                        course_key=class_unit.course_key, usage_key=usage_key)
            for order, usage_key in enumerate(lessons, start=1)
        ]

    ClassLesson.objects.bulk_create(class_lessons, ignore_conflicts=True)


@receiver(pre_save, sender=Class)
def gen_class_changed(sender, instance, *args, **kwargs):
    gen_class_qs = Class.objects.filter(pk=instance.pk)
    if gen_class_qs.exists() and gen_class_qs.first().program:
        return

    if instance.program:
        # enroll students to the program
        genplus_learning_tasks.enroll_class_students_to_program.apply_async(
            args=[instance.pk, instance.program.pk],
            countdown=settings.PROGRAM_ENROLLMENT_COUNTDOWN,
        )

        # give staff access to teachers
        genplus_learning_tasks.allow_program_access_to_class_teachers.apply_async(
            args=[instance.pk, instance.program.pk],
            countdown=settings.PROGRAM_ENROLLMENT_COUNTDOWN,
        )

        _create_class_unit_and_lessons(instance)


@receiver(m2m_changed, sender=Class.students.through)
def class_students_changed(sender, instance, action, **kwargs):
    pk_set = kwargs.pop('pk_set', None)
    if not pk_set:
        return

    if action == "post_add":
        if isinstance(instance, Class) and instance.program:
            genplus_learning_tasks.enroll_class_students_to_program.apply_async(
                args=[instance.pk, instance.program.pk],
                kwargs={
                    'class_student_ids': list(pk_set),
                },
                countdown=settings.PROGRAM_ENROLLMENT_COUNTDOWN
            )
    if action == "pre_remove":
        if isinstance(instance, Class) and instance.program:
            genplus_learning_tasks.unenroll_class_students_from_program.apply_async(
                args=[instance.pk, instance.program.pk],
                kwargs={
                    'class_student_ids': list(pk_set),
                },
                countdown=settings.PROGRAM_ENROLLMENT_COUNTDOWN
            )

    if action == 'pre_add':
        # create gen_log for the adding student in class
        GenLog.create_student_log(instance, list(pk_set), GenLogTypes.STUDENT_ADDED_TO_CLASS)

    if action == 'post_remove':
        # create gen_log for the removal of student
        GenLog.create_student_log(instance, list(pk_set), GenLogTypes.STUDENT_REMOVED_FROM_CLASS)


@receiver(post_save, sender=BlockCompletion)
def problem_raw_score_changed_handler(sender, **kwargs):
    instance = kwargs['instance']
    course_id = str(instance.context_key)
    if not instance.context_key.is_course:
        return
    usage_id = str(instance.block_key)
    user_id = instance.user_id

    genplus_learning_tasks.update_unit_and_lesson_completions.apply_async(
        args=[user_id, course_id, usage_id]
    )


# capture activity on lesson completion
@receiver(post_save, sender=UnitBlockCompletion)
def create_activity_on_lesson_completion(sender, instance, created, **kwargs):
    if instance.is_complete and instance.block_type == 'chapter':
        Activity.objects.create(
            actor=instance.user.gen_user.student,
            type=ActivityTypes.LESSON_COMPLETION,
            action_object=instance,
            target=instance.user.gen_user.student
        )


@receiver(pre_delete, sender=ProgramEnrollment)
def delete_course_enrollments(sender, instance, **kwargs):
    course_ids = instance.program.all_units_ids
    CourseEnrollment.objects.filter(user=instance.student.gen_user.user, course__in=course_ids).delete()
    # Create GenLog for Program Enrollment Deletion
    try:
        details = {
            'program': instance.program.year_group.name,
            'class': instance.gen_class.name
        }
        GenLog.program_enrollment_log(instance.student.gen_user.email,
                                      details=details)
    except Exception as e:
        log.exception(str(e))


@receiver(pre_delete, sender=Program)
def program_deleted(sender, instance, **kwargs):
    ProgramCache.clear_mapping_for_all_courses(instance)


@receiver(post_save, sender=Program)
def program_updated(sender, instance, created, **kwargs):
    if not created:
        ProgramCache.clear_mapping_for_all_courses(instance)
