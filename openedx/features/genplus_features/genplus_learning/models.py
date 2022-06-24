import statistics

from django.db import models
from django.conf import settings
from django_extensions.db.models import TimeStampedModel

from six import text_type
from xmodule.modulestore.django import modulestore
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from opaque_keys.edx.django.models import CourseKeyField, UsageKeyField
from .utils import get_section_completion_percentage, get_lms_link_for_unit


class Skill(TimeStampedModel):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class YearGroup(TimeStampedModel):
    name = models.CharField(max_length=128, unique=True)
    year_of_programme = models.CharField(max_length=128)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    def __str__(self):
        return self.name


class Unit(models.Model):
    course_key = CourseKeyField(db_index=True, primary_key=True, max_length=255)
    year_group = models.ForeignKey(YearGroup, null=True, on_delete=models.SET_NULL, related_name='units')

    @property
    def display_name(self):
        return CourseOverview.objects.get(id=self.course_key).display_name_with_default

    @property
    def course_image_url(self):
        return f"{settings.LMS_ROOT_URL}{CourseOverview.objects.get(id=self.course_key).course_image_url}"

    @property
    def short_description(self):
        return CourseOverview.objects.get(id=self.course_key).short_description

    @property
    def is_locked(self):
        return all([lesson.is_locked for lesson in self.lessons.all()])

    @property
    def lms_url(self):
        return get_lms_link_for_unit(self.course_key)

    def get_user_progress(self, user):
        percentages = [lesson.get_user_progress(user) for lesson in self.lessons.all()]
        return round(statistics.fmean(percentages), 2) if percentages else 0

    def __str__(self):
        return text_type(self.course_key)


class Lesson(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='lessons')
    usage_key = UsageKeyField(max_length=255, db_index=True)
    is_locked = models.BooleanField(default=False)

    class Meta:
        unique_together = ("unit", "usage_key")

    def get_user_progress(self, user):
        return get_section_completion_percentage(self.usage_key, user)
