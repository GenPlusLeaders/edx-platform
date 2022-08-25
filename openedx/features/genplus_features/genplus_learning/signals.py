import logging
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed, pre_save

from completion.models import BlockCompletion
from xmodule.modulestore.django import SignalHandler, modulestore
from openedx.features.genplus_features.genplus.models import Class, Teacher
import openedx.features.genplus_features.genplus_learning.tasks as genplus_learning_tasks
from openedx.features.genplus_features.genplus_learning.models import (
    Program, Unit, ClassUnit
)
from openedx.features.genplus_features.genplus_learning.access import allow_access
from openedx.features.genplus_features.genplus_learning.roles import ProgramInstructorRole
from openedx.features.genplus_features.genplus_learning.utils import update_class_lessons
log = logging.getLogger(__name__)


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):
    update_class_lessons(course_key)


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
        for teacher in instance.teachers.all():
            allow_access(instance.program, teacher.gen_user, ProgramInstructorRole.ROLE_NAME)

        # create class_units for units in this program
        class_units = [
            ClassUnit(gen_class=instance, unit=unit, course_key=unit.course.id)
            for unit in instance.program.units.all()
        ]
        ClassUnit.objects.bulk_create(class_units)


@receiver(m2m_changed, sender=Class.students.through)
def class_students_changed(sender, instance, action, **kwargs):
    pk_set = kwargs.pop('pk_set', None)
    if action == "post_add":
        if isinstance(instance, Class) and instance.program:
            genplus_learning_tasks.enroll_class_students_to_program.apply_async(
                args=[instance.pk, instance.program.pk],
                kwargs={
                    'class_student_ids': list(pk_set),
                },
                countdown=settings.PROGRAM_ENROLLMENT_COUNTDOWN
            )


@receiver(post_save, sender=BlockCompletion)
def set_unit_and_block_completions(sender, instance, created, **kwargs):
    if created:
        genplus_learning_tasks.update_unit_and_lesson_completions.apply_async(
            args=[instance.pk]
        )
