import statistics
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, views, viewsets, mixins, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import GenUser, Student, Class, Activity
from openedx.features.genplus_features.common.display_messages import SuccessMessages, ErrorMessages
from openedx.features.genplus_features.genplus.api.v1.permissions import IsStudentOrTeacher, IsTeacher, IsStudent
from openedx.features.genplus_features.genplus_learning.models import (Program, ProgramEnrollment,
                                                                       ClassUnit, ClassLesson,)
from openedx.features.genplus_features.genplus_learning.utils import get_absolute_url
from .serializers import ProgramSerializer, ClassStudentSerializer, ClassSummarySerializer, ActivitySerializer


class ProgramViewSet(viewsets.ModelViewSet):
    """
    Viewset for Lessons APIs
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudentOrTeacher]
    serializer_class = ProgramSerializer

    def get_queryset(self):
        gen_user = self.request.user.gen_user
        qs = Program.get_active_programs()
        if gen_user.is_student:
            enrollments = ProgramEnrollment.objects.filter(student=gen_user.student)
            program_ids = enrollments.values_list('program', flat=True)
            qs = Program.objects.filter(id__in=program_ids)
        return qs

    def get_serializer_context(self):
        context = super(ProgramViewSet, self).get_serializer_context()
        context.update({
            "gen_user": self.request.user.gen_user,
        })
        return context

    def get_permissions(self):
        permission_classes = [IsAuthenticated, ]
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
    search_fields = ['gen_user__user__username']

    def get_serializer_context(self):
        context = super(ClassStudentViewSet, self).get_serializer_context()
        group_id = self.kwargs.get('group_id', None)
        if group_id:
            gen_class = get_object_or_404(Class, group_id=group_id)
            class_units = ClassUnit.objects.select_related('unit')
            context['class_units'] = class_units.filter(gen_class=gen_class).order_by('unit__order')
            context['request'] = self.request
            return context

    def get_queryset(self):
        group_id = self.kwargs.get('group_id', None)
        try:
            gen_class = Class.objects.prefetch_related('students').get(group_id=group_id)
        except Class.DoesNotExist:
            return Student.objects.none()
        return gen_class.students.select_related('gen_user__user').all()


class ClassSummaryViewSet(mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ClassSummarySerializer
    queryset = Class.objects.all()
    lookup_field = 'group_id'

    def retrieve(self, request, group_id=None):  # pylint: disable=unused-argument
        """
        Returns the summary for a Class
        """
        gen_class = self.get_object()
        class_units = ClassUnit.objects.select_related('gen_class', 'unit').prefetch_related('class_lessons')
        class_units = class_units.filter(gen_class=gen_class)
        data = self.get_serializer(class_units, many=True).data

        for i in range(len(data)):
            lessons = data[i]['class_lessons']
            data[i]['unit_progress'] = round(statistics.fmean([lesson['class_lesson_progress']
                                                               for lesson in lessons])) if lessons else 0

        gen_class_data = {
            'school_name': gen_class.school.name,
            'class_name': gen_class.name,
            'class_image': get_absolute_url(request, gen_class.image),
            'results': data,
        }

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
        gen_class = request.user.gen_user.student.classes.first()
        if gen_class:
            data = {
                'progress': self.get_progress(gen_class)
            }
            return Response(data, status.HTTP_200_OK)

        return Response(ErrorMessages.NOT_A_PART_OF_PROGRAMME, status.HTTP_400_BAD_REQUEST)

    def get_progress(self, gen_class):
        gen_user = self.request.user.gen_user
        units_count = gen_class.program.units.count()
        average_progress = 0
        program_data = ProgramSerializer(gen_class.program, context={'gen_user', gen_user}).data
        if program_data and units_count > 0:
            average_progress += sum(item['progress'] for item in program_data['units']) / units_count

        return {
            'average_progress': average_progress,
            'units_progress': program_data
        }


class ActivityAPIView(ListAPIView):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = ActivitySerializer

    def get_queryset(self):
        student = self.request.user.gen_user.student
        return Activity.objects.student_activities(student_id=student.id)

