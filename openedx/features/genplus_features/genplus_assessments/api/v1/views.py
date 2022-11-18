import logging
from rest_framework import views, viewsets
from opaque_keys.edx.keys import CourseKey
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import Class
from openedx.features.genplus_features.genplus_assessments.models import UserResponse, UserRating
from openedx.features.genplus_features.genplus.api.v1.permissions import IsTeacher
from .serializers import ClassSerializer, TextAssessmentSerializer, RatingAssessmentSerializer
from openedx.features.genplus_features.genplus_assessments.utils import (
    build_students_result,
)

log = logging.getLogger(__name__)


class ClassFilterViewSet(views.APIView):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ClassSerializer

    def get(self,request, **kwargs):
        class_id = kwargs.get('class_id', None)
        try:
            gen_class = Class.objects.get(pk=class_id)
            gen_class_data = ClassSerializer(gen_class).data
        except Class.DoesNotExist:
            return Class.objects.none()
        return Response(gen_class_data)

class StudentAnswersView(viewsets.ViewSet):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]

    def students_problem_response(self, request, **kwargs):
        class_id = kwargs.get('class_id', None)
        student_id = request.query_params.get('student_id',None)
        students = []
        if student_id == "all":
            students = list(Class.objects.prefetch_related('students').get(pk=class_id).students.values_list('gen_user__user_id',flat=True))
        else:
            students.append(student_id)
        course_id = request.query_params.get('course_id',None)
        course_key = CourseKey.from_string(course_id)
        problem_locations = request.query_params.get('problem_locations',None)
        filter_type = request.query_params.get('filter',None)

        response = build_students_result(
            user_id=self.request.user.id,
            course_key=course_key,
            usage_key_str=problem_locations,
            student_list=students,
            filter_type=filter_type,
        )

        return Response(response)

class SkillAssessmentView(viewsets.ViewSet):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TextAssessmentSerializer, RatingAssessmentSerializer

    def skill_assessment_response(self, request, **kwargs):
        text_assessment = UserResponse.objects.filter(class_id=kwargs.get('class_id'))
        rating_assessment = UserRating.objects.filter(class_id=kwargs.get('class_id'))

        context = {
            "request": request,
        }

        text_assessment_data = TextAssessmentSerializer(text_assessment, many=True, context=context).data
        rating_assessment_data = RatingAssessmentSerializer(rating_assessment, many=True, context=context).data
        responses = text_assessment_data + rating_assessment_data
        final_response = {}
        final_response['aggregate_all_problem'] = {}
        final_response['aggregate_all_problem']['total_students'] = Class.objects.get(pk=kwargs.get('class_id')).students.count()
        final_response['aggregate_all_problem']['summation_problem_score'] = 0
        final_response['aggregate_all_problem']['students_score_start_of_year'] = 0
        final_response['aggregate_all_problem']['students_score_end_of_year'] = 0
        final_response['aggregate_skill'] = {}
        final_response['aggregate_single_problem'] = {}
        aggregate_result =  {}
        aggregate_skill =  {}
        for response in responses:
            response = dict(response)
            if response['problem_id'] not in aggregate_result:
                aggregate_result[response['problem_id']] = {}
                aggregate_result[response['problem_id']]['problem_id'] = response['problem_id']
                aggregate_result[response['problem_id']]['assessment_type'] = "text_assessment" if 'score' in response else "rating_assessment"
                aggregate_result[response['problem_id']]['skill'] = response['skill']
                aggregate_result[response['problem_id']]['score_start_of_year'] = 0
                aggregate_result[response['problem_id']]['score_end_of_year'] = 0
                aggregate_result[response['problem_id']]['count_response_start_of_year'] = 0
                aggregate_result[response['problem_id']]['count_response_end_of_year'] = 0
                if response['assessment_time'] == "start_of_year":
                    #aggregate_result[response['problem_id']]['course_id_start_of_year'] = response['course_id']
                    final_response['aggregate_all_problem']['summation_problem_score'] += 5
                    final_response['aggregate_all_problem']['students_score_start_of_year'] += response['score'] if 'score' in response else response['rating']
                    aggregate_result[response['problem_id']]['usage_id_start_of_year'] = response['usage_id']
                    aggregate_result[response['problem_id']]['score_start_of_year'] += response['score'] if 'score' in response else response['rating']
                    aggregate_result[response['problem_id']]['count_response_start_of_year'] += 1
                else:
                    #aggregate_result[response['problem_id']]['course_id_end_of_year'] = response['course_id']
                    final_response['aggregate_all_problem']['students_score_end_of_year'] += response['score'] if 'score' in response else response['rating']
                    aggregate_result[response['problem_id']]['usage_id_end_of_year'] = response['usage_id']
                    aggregate_result[response['problem_id']]['score_end_of_year'] += response['score'] if 'score' in response else response['rating']
                    aggregate_result[response['problem_id']]['count_response_end_of_year'] += 1
            else:
                if response['assessment_time'] == "start_of_year":
                    #aggregate_result[response['problem_id']]['course_id_start_of_year'] = response['course_id']
                    final_response['aggregate_all_problem']['students_score_start_of_year'] += response['score'] if 'score' in response else response['rating']
                    aggregate_result[response['problem_id']]['usage_id_start_of_year'] = response['usage_id']
                    aggregate_result[response['problem_id']]['score_start_of_year'] += response['score'] if 'score' in response else response['rating']
                    aggregate_result[response['problem_id']]['count_response_start_of_year'] += 1
                else:
                    #aggregate_result[response['problem_id']]['course_id_end_of_year'] = response['course_id']
                    final_response['aggregate_all_problem']['students_score_end_of_year'] += response['score'] if 'score' in response else response['rating']
                    aggregate_result[response['problem_id']]['usage_id_end_of_year'] = response['usage_id']
                    aggregate_result[response['problem_id']]['score_end_of_year'] += response['score'] if 'score' in response else response['rating']
                    aggregate_result[response['problem_id']]['count_response_end_of_year'] += 1
        for response in responses:
            response = dict(response)
            if response['skill'] not in aggregate_skill:
                aggregate_skill[response['skill']] = {}
                aggregate_skill[response['skill']]['skill'] = response['skill']
                aggregate_skill[response['skill']]['score_start_of_year'] = 0
                aggregate_skill[response['skill']]['score_end_of_year'] = 0
                if response['assessment_time'] == "start_of_year":
                    aggregate_skill[response['skill']]['score_start_of_year'] += response['score'] if 'score' in response else response['rating']
                else:
                    aggregate_skill[response['skill']]['score_end_of_year'] += response['score'] if 'score' in response else response['rating']
            else:
                if response['assessment_time'] == "start_of_year":
                    aggregate_skill[response['skill']]['score_start_of_year'] += response['score'] if 'score' in response else response['rating']
                else:
                    aggregate_skill[response['skill']]['score_end_of_year'] += response['score'] if 'score' in response else response['rating']

        final_response['aggregate_all_problem']['count_response_start_of_year'] = aggregate_result[next(iter(aggregate_result))]['count_response_start_of_year']
        final_response['aggregate_all_problem']['count_response_end_of_year'] = aggregate_result[next(iter(aggregate_result))]['count_response_end_of_year']
        final_response['aggregate_single_problem'].update(aggregate_result)
        final_response['aggregate_skill'].update(aggregate_skill)
        return Response(final_response)

    
