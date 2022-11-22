from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from opaque_keys.edx.django.models import CourseKeyField  # pylint: disable=import-error

from openedx.features.genplus_features.genplus.models import Skill


class Assessment(models.Model):
    user_id = models.CharField(max_length=500)
    course_id = CourseKeyField(max_length=255, blank=True, null=True, default=None)
    usage_id = models.CharField(max_length=500, blank=True, null=True, default=None)
    class_id = models.CharField(max_length=500, blank=True, null=True, default=None)
    problem_id = models.CharField(max_length=500, blank=True, null=True, default=None)
    assessment_time = models.CharField(max_length=500, blank=True, null=True, default=None) 
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateField(auto_now_add=True, blank=True)
    class Meta:
        abstract = True

class UserResponse(Assessment):
    student_response = models.TextField(blank=True, null=True, default=None)
    score = models.IntegerField(blank=True, null=True, default=0)
    class Meta:
        verbose_name = 'Response Model'

    def __str__(self):
        return "Score:{} by {}".format(self.score, self.user_id)
    
class UserRating(Assessment):
    rating = models.IntegerField(db_index=True, default=1, validators=[MaxValueValidator(5),MinValueValidator(1)])
    class Meta:
        verbose_name = 'Rating Model'

    def __str__(self):
        return "Rating:{} by {}".format(self.rating, self.user_id)
