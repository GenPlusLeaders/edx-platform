from django.contrib import admin
from openedx.features.genplus_features.genplus_assessments.models import UserResponse, UserRating, SkillAssessmentResponse, SkillAssessmentQuestion
from .constants import SkillReflectionQuestionType

class BaseModelAdmin(admin.ModelAdmin):
    def __init__(self, model, admin_site):
        self.model = model
        super().__init__(model, admin_site)
        self.list_display = [field.name for field in self.model._meta.get_fields()]


@admin.register(UserResponse)
class UserResponseAdmin(BaseModelAdmin):
    pass


@admin.register(UserRating)
class UserRatingAdmin(BaseModelAdmin):
    pass


@admin.register(SkillAssessmentQuestion)
class SkillAssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ('program', 'question_number', 'start_unit', 'start_unit_location',
                    'end_unit', 'end_unit_location', 'skill',)
    readonly_fields = ('program', 'question_number', 'start_unit', 'start_unit_location',
                       'end_unit', 'end_unit_location', 'skill',)


@admin.register(SkillAssessmentResponse)
class SkillAssessmentResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_program', 'get_question_number', 'get_question_skill', 'get_question_type',
                    'response_time', 'earned_score', 'total_score', 'created', 'modified',)
    readonly_fields = ('user', 'question', 'earned_score', 'total_score', 'response_time',
                       'question_response', 'created', 'modified',)
    search_fields = ('user__email',)

    def get_program(self, obj):
        return obj.question.program

    def get_question_number(self, obj):
        return obj.question.question_number


    def get_question_skill(self, obj):
        try:
            return obj.question.skill.name
        except AttributeError:
            return '-'

    def get_question_type(self, obj):
        try:
            return SkillAssessmentResponse(obj.question.problem_type).name
        except AttributeError:
            return '-'

    get_program.short_description = 'Program'
    get_question_number.short_description = 'Question No'
    get_question_skill.short_description = 'Question Skill'
    get_question_type.short_description = 'Question Type'
