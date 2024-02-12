from django.db.models.signals import post_save
from django.dispatch import receiver

from completion_aggregator.models import Aggregator
from openedx.features.genplus_features.genplus.constants import ActivityTypes
from openedx.features.genplus_features.genplus.models import Activity
from openedx.features.genplus_features.genplus_badges.events.completion import program_badge_check, unit_badge_check

from .models import BoosterBadgeAward


@receiver(post_save, sender=Aggregator)
def create_unit_badge(sender, instance, **kwargs):
    if instance.aggregation_name == 'course' and instance.percent == 1:
        unit_badge_check(instance.user, instance.course_key)


@receiver(post_save, sender=Aggregator)
def create_program_badge(sender, instance, **kwargs):
    if instance.aggregation_name == 'course' and instance.percent == 1:
        program_badge_check(instance.user, instance.course_key)


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
