import random
from rest_framework import serializers

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.genplus_features.genplus_learning.models import (
    Program,
    ProgramEnrollment,
    Unit,
    ClassLesson,
    ClassUnit,
    UnitCompletion,
    UnitBlockCompletion,
)
from openedx.features.genplus_features.genplus_learning.constants import ProgramEnrollmentStatuses
from openedx.features.genplus_features.genplus_learning.utils import calculate_class_lesson_progress
from openedx.features.genplus_features.genplus.models import Student


class UnitSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = ('id', 'display_name', 'short_description',
                  'banner_image_url', 'is_locked', 'lms_url',
                  'progress')

    def get_id(self, obj):
        return str(obj.course.id)

    def get_is_locked(self, obj):
        units_context = self.context.get("units_context")
        return units_context[obj.pk]['is_locked']

    def get_progress(self, obj):
        units_context = self.context.get("units_context")
        return units_context[obj.pk]['progress']


class ProgramSerializer(serializers.ModelSerializer):
    units = serializers.SerializerMethodField()
    year_group_name = serializers.CharField(source='year_group.name')
    program_name = serializers.CharField(source='year_group.program_name')

    class Meta:
        model = Program
        fields = ('program_name', 'year_group_name', 'units')

    def get_units(self, obj):
        gen_user = self.context.get('gen_user')
        units = obj.units.all()
        completions = UnitCompletion.objects.filter(
            user=gen_user.user,
            course_key__in=units.values_list('course', flat=True)
        )
        units_context = {}

        for unit in units:
            units_context[unit.pk] = {}
            if gen_user.is_student:
                enrollment = gen_user.student.program_enrollments.get(program=obj)
                completion = completions.filter(user=gen_user.user, course_key=unit.course.id).first()
                units_context[unit.pk] = {
                    'is_locked': unit.is_locked(enrollment.gen_class),
                    'progress': completion.progress if completion else 0,
                }
            else:
                units_context[unit.pk] = {
                    'is_locked': False,
                    'progress': None,
                }

        return UnitSerializer(units, many=True, read_only=True, context={'units_context': units_context}).data


class ClassLessonSerializer(serializers.ModelSerializer):
    class_lesson_progress = serializers.SerializerMethodField()

    class Meta:
        model = ClassLesson
        fields = ('id', 'is_locked', 'class_lesson_progress', 'lms_url')

    def get_class_lesson_progress(self, obj):
        return calculate_class_lesson_progress(obj.course_key, obj.usage_key, obj.class_unit.gen_class)


class ClassSummarySerializer(serializers.ModelSerializer):
    class_lessons = ClassLessonSerializer(many=True, read_only=True)
    display_name = serializers.CharField(source="unit.display_name")
    school_name = serializers.CharField(source="gen_class.school.name")
    class_image = serializers.CharField(source="gen_class.image")
    class_name = serializers.CharField(source="gen_class.name")

    class Meta:
        model = ClassUnit
        fields = ('id', 'display_name', 'is_locked', 'class_lessons', 'school_name', 'class_image', 'class_name')


class ClassStudentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    profile_pic = serializers.SerializerMethodField()
    total_badges = serializers.SerializerMethodField()
    skills_assessment = serializers.SerializerMethodField()
    unit_lesson_completion = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ('username', 'profile_pic', 'total_badges', 'skills_assessment', 'unit_lesson_completion')

    def get_profile_pic(self, obj):
        profile = obj.character.profile_pic if obj.character else None
        return profile.url if profile else None

    def get_total_badges(self, obj):
        return random.randint(0, 5)

    def get_skills_assessment(self, obj):
        return True

    def get_unit_lesson_completion(self, obj):
        results = []
        class_units = self.context.get('class_units')
        for class_unit in class_units:
            progress = {'unit_display_name': class_unit.unit.display_name}
            chapters = class_unit.class_lessons.all()
            chapter_keys = chapters.values_list('usage_key', flat=True)
            chapter_count = chapters.count()
            completion_qs = UnitBlockCompletion.objects.filter(user=obj.user,
                                                               usage_key__in=chapter_keys,
                                                               block_type='chapter')
            block_completions = completion_qs.values_list('is_complete', flat=True)
            progress['lessons_completions'] = block_completions
            progress['total_lessons'] = chapter_count
            results.append(progress)
        return results
