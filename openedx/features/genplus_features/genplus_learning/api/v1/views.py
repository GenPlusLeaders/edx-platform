from django.shortcuts import get_object_or_404
from rest_framework import generics, status, views, viewsets, mixins, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.constants import GenUserRoles
from openedx.features.genplus_features.genplus.models import GenUserProfile, Student, Class, Activity
from openedx.features.genplus_features.common.display_messages import SuccessMessages, ErrorMessages
from openedx.features.genplus_features.genplus.api.v1.permissions import IsStudentOrTeacher, IsTeacher, IsStudent
from openedx.features.genplus_features.genplus_learning.models import (Program, ProgramEnrollment,
                                                                       ClassUnit, ClassLesson, UnitCompletion,
                                                                       UnitBlockCompletion)
from openedx.features.genplus_features.genplus_learning.utils import get_absolute_url
from .serializers import ProgramSerializer, ClassStudentSerializer, ActivitySerializer, ClassUnitSerializer
from openedx.features.genplus_features.genplus.api.v1.serializers import ClassSummarySerializer


class ProgramViewSet(viewsets.ModelViewSet):
    """
    Viewset for Lessons APIs
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudentOrTeacher]
    serializer_class = ProgramSerializer

    def get_queryset(self):
        user = self.request.user
        if user.gen_user.is_student:
            enrollments = ProgramEnrollment.visible_objects.filter(student=user)
            program_ids = enrollments.values_list('program', flat=True)
            qs = Program.objects.filter(id__in=program_ids)
        else:
            qs = Program.get_active_programs()
        return qs

    def get_serializer_context(self):
        context = super(ProgramViewSet, self).get_serializer_context()
        context.update({
            "user": self.request.user,
        })
        return context

    def get_permissions(self):
        permission_classes = [IsAuthenticated,]
        if self.action == 'list':
            permission_classes.append(IsStudentOrTeacher)
        else:
            permission_classes.append(IsTeacher)
        return [permission() for permission in permission_classes]


class ClassStudentViewSet(mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ClassStudentSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username']

    def get_serializer_context(self):
        context = super(ClassStudentViewSet, self).get_serializer_context()
        class_id = self.kwargs.get('pk', None)
        if class_id:
            gen_class = get_object_or_404(Class, pk=class_id)
            context['class_units'] = ClassUnit.objects.select_related('unit').filter(gen_class=gen_class)
            context['request'] = self.request
        return context

    def get_queryset(self):
        class_id = self.kwargs.get('pk', None)
        try:
            gen_class = Class.objects.prefetch_related('gen_users').get(pk=class_id)
        except Class.DoesNotExist:
            return Student.objects.none()
        return gen_class.gen_users.select_related('user').filter(role=GenUserRoles.STUDENT)


class ClassSummaryViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ClassSummarySerializer
    queryset = Class.visible_objects.all()

    def retrieve(self, request, pk=None):  # pylint: disable=unused-argument
        """
        Returns the summary for a Class
        """
        gen_class = self.get_object()
        class_units = ClassUnit.objects.select_related('gen_class', 'unit').prefetch_related('class_lessons')
        class_units = class_units.filter(gen_class=gen_class)
        class_units_data = ClassUnitSerializer(class_units, many=True).data
        gen_class_data = self.get_serializer(gen_class).data
        gen_class_data['results'] = class_units_data
        return Response(gen_class_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['put'])
    def unlock_lesson(self, request, lesson_id=None):  # pylint: disable=unused-argument
        """
       unlock the lesson of the unit
        """
        lesson = get_object_or_404(ClassLesson, pk=lesson_id)
        if not lesson.is_locked:
            return Response(ErrorMessages.LESSON_ALREADY_UNLOCKED, status.HTTP_204_NO_CONTENT)
        lesson.is_locked = False
        lesson.save()
        return Response(SuccessMessages.LESSON_UNLOCKED, status.HTTP_204_NO_CONTENT)


class StudentDashboardAPIView(APIView):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):  # pylint: disable=unused-argument
        """
       student dashboard data
        """
        user = request.user
        gen_class = user.gen_user.active_class
        if gen_class and gen_class.program:
            data = {
                'progress': self.get_progress(user, gen_class),
                'next_lesson': self.get_next_lesson(user, gen_class)
            }
            program_progress = data['progress']['average_progress']
            character_state = student.character.get_state(program_progress)
            data.update({'character_video_url': get_absolute_url(request, character_state)})
            return Response(data, status.HTTP_200_OK)

        return Response(ErrorMessages.NOT_A_PART_OF_PROGRAMME, status.HTTP_400_BAD_REQUEST)

    def get_progress(self, user, gen_class):
        units_count = gen_class.program.units.count()
        average_progress = 0
        program_data = ProgramSerializer(gen_class.program, context={'user': user}).data
        if program_data and units_count > 0:
            average_progress += sum(item['progress'] for item in program_data['units']) // units_count

        return {
            'average_progress': average_progress,
            'units_progress': program_data
        }

    def get_next_lesson(self, user, gen_class):
        class_units = gen_class.class_units.all()
        course_keys = class_units.values_list('course_key', flat=True)
        user_completions = UnitCompletion.objects.filter(user=user)

        # User has not started a course yet.
        if not user_completions:
            next_unit = class_units.first()
            next_lesson = next_unit.class_lessons.first()
            return {'url': next_lesson.lms_url, 'display_name': next_lesson.display_name}

        incomplete_unit_completion = user_completions.filter(is_complete=False,
                                                             course_key__in=course_keys).first()

        if incomplete_unit_completion:
            next_unit = class_units.filter(course_key=incomplete_unit_completion.course_key).first()
            next_unit_lessons = next_unit.class_lessons.filter(is_locked=False)
            for lesson in next_unit_lessons:
                lesson_completion = UnitBlockCompletion.objects.filter(user=user,
                                                                       usage_key=lesson.usage_key).first()
                if not lesson_completion or not lesson_completion.is_complete:
                    return {'url': lesson.lms_url, 'display_name': lesson.display_name}
        return None


class ActivityViewSet(mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = ActivitySerializer

    def get_queryset(self):
        user = self.request.user
        return Activity.objects.student_activities(user_id=user.id)

    @action(detail=True, methods=['put'])
    def read_activity(self, request, pk=None):  # pylint: disable=unused-argument
        instance = self.get_object()
        instance.is_read = True
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
