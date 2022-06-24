from rest_framework import generics, status, views, viewsets
from rest_framework.permissions import IsAuthenticated

from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import GenUser, Student
from openedx.features.genplus_features.genplus_learning.models import YearGroup
from .serializers import YearGroupSerializer


class YearGroupViewSet(viewsets.ModelViewSet):
    """
    Viewset for YearGroup APIs
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated]
    serializer_class = YearGroupSerializer

    def get_queryset(self):
        qs = YearGroup.objects.all()
        genuser = self.request.user.genuser
        if genuser.is_student:
            qs = qs.filter(students=genuser.student)

        return qs
