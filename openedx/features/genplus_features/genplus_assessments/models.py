from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from jsonfield import JSONField
from django_extensions.db.models import TimeStampedModel

from opaque_keys.edx.django.models import CourseKeyField, UsageKeyField  # pylint: disable=import-error

from .constants import (
    SkillAssessmentTypes,
    SkillAssessmentResponseTime,
    SkillReflectionQuestionType,
)
from openedx.features.genplus_features.genplus.models import Skill, Class
from openedx.features.genplus_features.genplus_learning.models import Program

USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class Assessment(TimeStampedModel):
    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    course_id = CourseKeyField(max_length=255, db_index=True)
    usage_id = UsageKeyField(max_length=255, db_index=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    gen_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True)
    problem_id = models.CharField(max_length=64)
    assessment_time = models.CharField(max_length=64)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    class Meta:
        abstract = True

class UserResponse(Assessment):
    student_response = models.TextField(blank=True, null=True, default=None)
    score = models.IntegerField(blank=True, null=True, default=0)
    class Meta:
        verbose_name = 'User Text Responses'

    def __str__(self):
        return "Score:{} by {}".format(self.score, self.user_id)

class UserRating(Assessment):
    rating = models.IntegerField(db_index=True, default=1, validators=[MaxValueValidator(5),MinValueValidator(1)])
    class Meta:
        verbose_name = 'User Rating Responses'

    def __str__(self):
        return "Rating:{} by {}".format(self.rating, self.user_id)


class SkillAssessmentQuestion(models.Model):
    class Meta:
        unique_together = ('program', 'start_unit_location', 'end_unit_location')
        ordering = ('question_number',)

    question_number = models.PositiveIntegerField(default=0, blank=False, null=False)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    start_unit = CourseKeyField(max_length=255, db_index=True)
    start_unit_location = UsageKeyField(max_length=255, db_index=True)
    end_unit = CourseKeyField(max_length=255, db_index=True)
    end_unit_location = UsageKeyField(max_length=255, db_index=True)
    skill = models.ForeignKey(Skill, null=True, on_delete=models.CASCADE)
    problem_type = models.IntegerField(choices=SkillReflectionQuestionType.choices(), null=True)


class SkillAssessmentResponse(TimeStampedModel):
    SKILL_ASSESSMENT_RESPONSE_TIME = SkillAssessmentResponseTime.__MODEL_CHOICES__
    SKILL_ASSESSMENT_TYPE_CHOICES = SkillAssessmentTypes.__MODEL_CHOICES__
    class Meta:
        unique_together = ('user', 'question', 'response_time')

    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(SkillAssessmentQuestion, on_delete=models.CASCADE, related_name='submissions')
    earned_score = models.FloatField(blank=True, null=True, default=0.0)
    total_score = models.FloatField(blank=True, null=True, default=6.0)
    response_time = models.CharField(max_length=32, null=True, choices=SKILL_ASSESSMENT_RESPONSE_TIME)
    skill_assessment_type = models.CharField(max_length=32, null=True, choices=SKILL_ASSESSMENT_TYPE_CHOICES)
    question_response = JSONField(blank=True, null=True)
    problem_location = UsageKeyField(max_length=255, db_index=True, blank=True, null=True)
