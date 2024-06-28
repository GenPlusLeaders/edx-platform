import logging
from completion.models import BlockCompletion
from django.dispatch import receiver
from django.db.models.signals import post_save
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.signals.signals import COURSE_COMPLETED
from openedx.features.genplus_features.genplus.models import Activity
from openedx.features.genplus_features.genplus.constants import ActivityTypes
from openedx.features.genplus_features.genplus_badges.events.completion import (
    unit_badge_check,
    program_badge_check
)
from .models import BoosterBadgeAward

logger = logging.getLogger(__name__)


@receiver(COURSE_COMPLETED, sender=BlockCompletion)
def create_unit_badge(sender, user, course_key, **kwargs):
    logger.info(f'Received course completed signal {str(user)},{str(course_key)}')
    if isinstance(course_key, str):
        course_key = CourseKey.from_string(course_key)

    try:
        unit_badge_check(user, course_key)
        program_badge_check(user, course_key)
    except Exception as ex:
        logger.exception(f'Something went wrong {str(ex)}')

# capture activity on badge award
@receiver(post_save, sender=BoosterBadgeAward)
def create_activity_on_badge_award(sender, instance, created, **kwargs):
    if created:
        Activity.objects.create(
            actor=instance.awarded_by.gen_user.teacher,
            type=ActivityTypes.BADGE_AWARD,
            action_object=instance,
            target=instance.user.gen_user.student
        )
