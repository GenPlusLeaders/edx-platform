from django.contrib import admin
from openedx.features.genplus_features.genplus_assessments.models import UserResponse, UserRating


@admin.register(UserResponse)
class UserResponseAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'course_id', 'usage_id', 'class_id', 'problem_id', 'assessment_time', 'skill', 'student_response', 'score')

@admin.register(UserRating)
class UserResponseAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'course_id', 'usage_id', 'class_id', 'problem_id', 'assessment_time', 'skill', 'rating')