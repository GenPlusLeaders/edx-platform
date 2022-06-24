from django.middleware import csrf
from django.utils.decorators import method_decorator

from rest_framework import generics, status, views, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from openedx.core.djangoapps.cors_csrf.decorators import ensure_csrf_cookie_cross_domain
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import GenUser, Character, Teacher, Student
from .serializers import (CharacterSerializer, TeacherProfileSerializer,
                            StudentProfileSerializer)
from .permissions import IsStudent
from .messages import SuccessMessage, ErrorMessages


class UserInfo(views.APIView):
    """
    API for genplus user information
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        get user's basic info
        """
        try:
            gen_user = GenUser.objects.get(user=self.request.user)
        except GenUser.DoesNotExist:
            return Response(ErrorMessages.INTERNAL_SERVER, status=status.HTTP_400_BAD_REQUEST)

        user_info = {
            'id': self.request.user.id,
            'name': self.request.user.profile.name,
            'username': self.request.user.username,
            'csrf_token': csrf.get_token(self.request),
            'role': gen_user.role
        }

        if gen_user.is_student:
            user_info.update({'onboarded': gen_user.student.onboarded})
            student = Student.objects.get(gen_user=gen_user)
            data = StudentProfileSerializer(instance=student).data
            user_info.update({'profile': data})
            
        if gen_user.is_teacher:
            teacher = Teacher.objects.get(gen_user=gen_user)
            data = TeacherProfileSerializer(instance=teacher).data
            user_info.update({'profile': data})

        return Response(status=status.HTTP_200_OK, data=user_info)
               
    @method_decorator(ensure_csrf_cookie_cross_domain)
    def post(self, *args, **kwargs):
        try:
            gen_user = GenUser.objects.get(user=self.request.user)
            if gen_user.is_teacher:
                teacher = Teacher.objects.get(gen_user=gen_user)
                serializer = TeacherProfileSerializer(teacher, data=self.request.data, 
                                                                        partial=True)
                serializer.is_valid(raise_exception=True)
                obj = serializer.save()
                image_url = 'media/' + str(obj.profile_image)
                data = {'message': SuccessMessage.PPOFILE_IMAGE_UPLOADED,
                        'url': image_url,
                        }
                        
            if gen_user.is_student:
                student = Student.objects.get(gen_user=gen_user)
                serializer = StudentProfileSerializer(student, data=self.request.data,
                                                                         partial=True)
                serializer.is_valid(raise_exception=True)
                obj = serializer.save()
                data = {'message': SuccessMessage.PPOFILE_IMAGE_UPLOADED,
                        'character_id': obj.character.id
                        }
            return Response(data=data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class CharacterViewSet(viewsets.ModelViewSet):
    """
    Viewset for character APIs
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated & IsStudent]
    serializer_class = CharacterSerializer
    queryset = Character.objects.all()

    @action(detail=True, methods=['post'])
    def select_character(self, request, pk=None):  # pylint: disable=unused-argument
        """
        select character at the time of onboarding or changing character from
        the profile
        """
        character = self.get_object()
        genuser = GenUser.objects.get(user=self.request.user)
        genuser.student.character = character
        if request.data.get("onboarded") and not genuser.student.onboarded:
            genuser.student.onboarded = True

        genuser.student.save()
        return Response(SuccessMessage.CHARACTER_SELECTED, status=status.HTTP_204_NO_CONTENT)
