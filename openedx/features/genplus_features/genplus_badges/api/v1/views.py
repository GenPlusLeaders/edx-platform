"""
API views for badges
"""
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from lms.djangoapps.badges.models import BadgeClass, BadgeAssertion
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus_learning.models import Program, ProgramEnrollment, YearGroup
from openedx.features.genplus_features.genplus_learning.constants import ProgramEnrollmentStatuses, ProgramStatuses
from openedx.features.genplus_features.genplus.api.v1.permissions import IsStudent, IsTeacher, IsStudentOrTeacher
from openedx.features.genplus_features.genplus.display_messages import SuccessMessages
from openedx.features.genplus_features.genplus_badges.models import BoosterBadge, BoosterBadgeAward
from .serializers import (ProgramBadgeSerializer, AwardBoosterBadgesSerializer,
                          BoosterBadgeSerializer, ClassBoosterBadgesSerializer)


class StudentProgramBadgeView(generics.ListAPIView):
    serializer_class = ProgramBadgeSerializer
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        gen_user = self.request.user.gen_user
        enrolled_programs = ProgramEnrollment.objects \
            .filter(student=gen_user.student,
                    status__in=ProgramEnrollmentStatuses.__VISIBLE__).order_by('created')

        enrolled_year_groups = enrolled_programs.values_list('program__year_group', flat=True).distinct().order_by()
        unenrolled_year_groups = YearGroup.objects.exclude(id__in=enrolled_year_groups)
        unenrolled_active_programs_slug = Program.objects \
            .filter(status=ProgramStatuses.ACTIVE, year_group__in=unenrolled_year_groups) \
            .values_list('slug', flat=True)
        enrolled_programs_slug = enrolled_programs.values_list('program__slug', flat=True)
        programs_slug = list(enrolled_programs_slug) + list(unenrolled_active_programs_slug)
        queryset = BadgeClass.objects.prefetch_related('badgeassertion_set') \
            .filter(issuing_component='genplus__program',
                    slug__in=programs_slug)
        return queryset

    def get_serializer_context(self):
        context = super(StudentProgramBadgeView, self).get_serializer_context()
        context.update({"user": self.request.user})
        return context


class AwardBoosterBadgesView(generics.CreateAPIView):
    serializer_class = AwardBoosterBadgesSerializer
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_serializer_context(self):
        context = super(AwardBoosterBadgesView, self).get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(SuccessMessages.BADGE_AWARDED, status=status.HTTP_201_CREATED)


class BoosterBadgeView(generics.ListAPIView):
    serializer_class = BoosterBadgeSerializer
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    pagination_class = None
    queryset = BoosterBadge.objects.select_related('skill').all()


class ClassBoosterBadgeView(generics.ListAPIView):
    serializer_class = ClassBoosterBadgesSerializer
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudentOrTeacher]
    pagination_class = None
    lookup_url_kwarg = 'username'

    def get_queryset(self):
        username = self.kwargs.get(self.lookup_url_kwarg, None)
        user = get_object_or_404(User, username=username)
        return BoosterBadgeAward.objects.filter(user=user)

