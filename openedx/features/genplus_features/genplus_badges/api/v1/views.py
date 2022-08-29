"""
API views for badges
"""
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus_learning.models import Program
from openedx.features.genplus_features.genplus.api.v1.permissions import IsStudent
from lms.djangoapps.badges.models import BadgeAssertion
from .serializers import ProgramBadgeSerializer


class StudentProgramBadgeView(generics.ListAPIView):

    serializer_class = ProgramBadgeSerializer
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        pass
