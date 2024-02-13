from django.db.models.signals import post_save
from django.dispatch import receiver

from openedx.features.genplus_features.genplus.constants import ActivityTypes
from openedx.features.genplus_features.genplus.models import Activity
from openedx.features.genplus_features.genplus_badges.events.completion import program_badge_check, unit_badge_check

from .models import BoosterBadgeAward
from django.contrib.auth.models import User
from completion_aggregator.dispatch import AggregatorUpdate


@receiver(AggregatorUpdate)
def create_unit_badge(sender, aggregation_data, **kwargs):
    course = next(
        filter(lambda aggregator: aggregator['aggregation_name'] == 'course', aggregation_data), None
    )
    if course and course['percent'] == 1:
        user = User.objects.get(pk=course['user'])
        unit_badge_check(user, course.course_key)


@receiver(AggregatorUpdate)
def create_program_badge(sender, aggregation_data, **kwargs):
    course = next(
        filter(lambda aggregator: aggregator['aggregation_name'] == 'course', aggregation_data), None
    )
    if course and course['percent'] == 1:
        user = User.objects.get(pk=course['user'])
        program_badge_check(user, course['course_key'])


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
