import json
import logging
from django.db.models import Q

from rest_framework import views, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import UsageKey, CourseKey

from openedx.features.course_experience.utils import get_course_outline_block_tree
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import Class
from openedx.features.genplus_features.genplus_assessments.models import UserResponse, UserRating
from openedx.features.genplus_features.genplus.api.v1.permissions import IsTeacher
from .serializers import ClassSerializer, TextAssessmentSerializer, RatingAssessmentSerializer
from openedx.features.genplus_features.genplus_assessments.utils import (
    build_students_result,
)
from lms.djangoapps.course_blocks.api import get_course_blocks

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

    def aggregate_assessments_response(self, request, **kwargs):
        import pdb
        pdb.set_trace()
        class_id = kwargs.get('class_id')
        student_id = request.query_params.get('student_id',None)
        if student_id != "all" and student_id is not None:
            text_assessment = UserResponse.objects.filter(user=student_id,gen_class=class_id)
            rating_assessment = UserRating.objects.filter(user=student_id,gen_class=class_id)
        else:
            text_assessment = UserResponse.objects.filter(gen_class=class_id)
            rating_assessment = UserRating.objects.filter(gen_class=class_id)
        text_assessment_data = TextAssessmentSerializer(text_assessment, many=True).data
        rating_assessment_data = RatingAssessmentSerializer(rating_assessment, many=True).data
        raw_data = text_assessment_data + rating_assessment_data
        response = {}
        response['aggregate_all_problem'] = {}
        response['aggregate_skill'] = {}
        response['single_assessment_result'] = {}
        response['aggregate_all_problem'] = self.get_aggregate_problems_result(raw_data, class_id)
        response['aggregate_skill'] = self.get_aggregate_skill_result(raw_data)
        response['single_assessment_result'] = self.get_assessment_result(raw_data)

        return Response(response)

    
    def single_assessment_response(self, request, **kwargs):
        class_id = kwargs.get('class_id')
        start_year_usasge_key = request.query_params.get('start_year_usasge_key',None)
        end_year_usasge_key = request.query_params.get('end_year_usasge_key',None)
        assessment_type = request.query_params.get('assessment_type',None)
        usage_key = UsageKey.from_string(start_year_usasge_key)
        response = {}
        store = modulestore()
        try:
            gen_class = Class.objects.get(pk=class_id)
            response['question_statement'] = store.get_item(usage_key).question_statement
            response['assessment_type'] = assessment_type
            response['total_respones'] = gen_class.students.count() * 2
            response['availaible_respones'] = 0
            response['student_response'] = {}
            if assessment_type == "text_assessment":
                text_assessment = UserResponse.objects.filter(Q(program=gen_class.program) & Q(gen_class=class_id) & Q(usage_id=start_year_usasge_key) | Q(usage_id=end_year_usasge_key))
                text_assessment_data = TextAssessmentSerializer(text_assessment, many=True).data
                raw_data = text_assessment_data
            else:
                rating_assessment = UserRating.objects.filter(Q(program=gen_class.program) & Q(gen_class=class_id) & Q(usage_id=start_year_usasge_key) | Q(usage_id=end_year_usasge_key))
                rating_assessment_data = RatingAssessmentSerializer(rating_assessment, many=True).data
                raw_data = rating_assessment_data

            students = gen_class.students.all()
            #prepare response against all the students in a class
            for student in students:
                response['student_response']['user_'+str(student.gen_user.user_id)] = {}
                response['student_response']['user_'+str(student.gen_user.user_id)]['full_name'] = student.gen_user.user.get_full_name()
                response['student_response']['user_'+str(student.gen_user.user_id)]['score_start_of_year'] = 0
                response['student_response']['user_'+str(student.gen_user.user_id)]['score_end_of_year'] = 0
                response['student_response']['user_'+str(student.gen_user.user_id)]['total_score'] = 5
                if assessment_type == "text_assessment":
                    response['student_response']['user_'+str(student.gen_user.user_id)]['response_start_of_year'] = None
                    response['student_response']['user_'+str(student.gen_user.user_id)]['response_end_of_year'] = None

            response.update(self.get_single_assessment_response(raw_data, response))
        except Exception as e:
            print(type(e))

        return Response(response)

    def get_aggregate_problems_result(self, raw_data, class_id):
        """
        Generate aggregate result for assessment on base of class as per the user state  under the
        ``problem_location`` root.
        Arguments:
            raw_data (list): data get from UserResponse and UserRating models.
        Returns:
                [Dict]: Returns a dictionaries
                containing the students aggregate class base result data.
        """
        problem_ids = {}
        aggregate_result = {}
        aggregate_result['total_students'] = Class.objects.get(pk=class_id).students.count()
        aggregate_result['accumulative_all_problem_score'] = 0
        aggregate_result['accumulative_score_start_of_year'] = 0
        aggregate_result['accumulative_score_end_of_year'] = 0
        aggregate_result['count_response_start_of_year'] = 0
        aggregate_result['count_response_end_of_year'] = 0
        for data in raw_data:
            data = dict(data)
            if data['problem_id'] not in problem_ids:
                problem_ids[data['problem_id']] = {}
                problem_ids[data['problem_id']]['count_response_start_of_year'] = 0
                problem_ids[data['problem_id']]['count_response_end_of_year'] = 0
                if data['assessment_time'] == "start_of_year":
                    problem_ids[data['problem_id']]['count_response_start_of_year'] += 1
                    aggregate_result['accumulative_all_problem_score'] += 5
                    aggregate_result['accumulative_score_start_of_year'] += data['score'] if 'score' in data else data['rating']
                else:
                    problem_ids[data['problem_id']]['count_response_end_of_year'] += 1
                    aggregate_result['accumulative_score_end_of_year'] += data['score'] if 'score' in data else data['rating']
            else:
                if data['assessment_time'] == "start_of_year":
                    problem_ids[data['problem_id']]['count_response_start_of_year'] += 1
                    aggregate_result['accumulative_score_start_of_year'] += data['score'] if 'score' in data else data['rating']
                else:
                    problem_ids[data['problem_id']]['count_response_end_of_year'] += 1
                    aggregate_result['accumulative_score_end_of_year'] += data['score'] if 'score' in data else data['rating']
        
        aggregate_result['count_response_start_of_year'] = problem_ids[next(iter(problem_ids))]['count_response_start_of_year'] if len(problem_ids) > 0 else 0
        aggregate_result['count_response_end_of_year'] = problem_ids[next(iter(problem_ids))]['count_response_end_of_year'] if len(problem_ids) > 0 else 0

        return aggregate_result

    def get_aggregate_skill_result(self, raw_data):
        """
        Generate aggregate result for assessment for web chart on base of skills as per the user state  under the
        ``problem_location`` root.
        Arguments:
            raw_data (list): data get from UserResponse and UserRating models.
        Returns:
                [Dict]: Returns a dictionaries
                containing the students aggregate skill base result data.
        """
        aggregate_result =  {}
        for data in raw_data:
            data = dict(data)
            if data['skill'] not in aggregate_result:
                aggregate_result[data['skill']] = {}
                aggregate_result[data['skill']]['skill'] = data['skill']
                aggregate_result[data['skill']]['score_start_of_year'] = 0
                aggregate_result[data['skill']]['score_end_of_year'] = 0
                if data['assessment_time'] == "start_of_year":
                    aggregate_result[data['skill']]['score_start_of_year'] += data['score'] if 'score' in data else data['rating']
                else:
                    aggregate_result[data['skill']]['score_end_of_year'] += data['score'] if 'score' in data else data['rating']
            else:
                if data['assessment_time'] == "start_of_year":
                    aggregate_result[data['skill']]['score_start_of_year'] += data['score'] if 'score' in data else data['rating']
                else:
                    aggregate_result[data['skill']]['score_end_of_year'] += data['score'] if 'score' in data else data['rating']

        return aggregate_result
    
    def get_assessment_result(self, raw_data):
        """
        Generate aggregate result for single assessment for bar and graph char on base of single assessment 
        as per the user state  under the ``problem_location`` root.
        Arguments:
            raw_data (list): data get from UserResponse and UserRating models.
        Returns:
                [Dict]: Returns a dictionaries
                containing the students aggregate result for single assessment.
        """
        store = modulestore()
        aggregate_result =  {}
        for data in raw_data:
            data = dict(data)
            usage_key = UsageKey.from_string(data['usage_id']).map_into_course(CourseKey.from_string(data['course_id']))
            if data['problem_id'] not in aggregate_result:
                aggregate_result[data['problem_id']] = {}
                aggregate_result[data['problem_id']]['problem_id'] = data['problem_id']
                aggregate_result[data['problem_id']]['problem_statement'] = store.get_item(usage_key).question_statement
                aggregate_result[data['problem_id']]['assessment_type'] = "text_assessment" if 'score' in data else "rating_assessment"
                aggregate_result[data['problem_id']]['skill'] = data['skill']
                aggregate_result[data['problem_id']]['score_start_of_year'] = 0
                aggregate_result[data['problem_id']]['score_end_of_year'] = 0
                aggregate_result[data['problem_id']]['count_response_start_of_year'] = 0
                aggregate_result[data['problem_id']]['count_response_end_of_year'] = 0
                if data['assessment_time'] == "start_of_year":
                    aggregate_result[data['problem_id']]['course_id_start_of_year'] = data['course_id']
                    aggregate_result[data['problem_id']]['usage_key_start_of_year'] = data['usage_id']
                    aggregate_result[data['problem_id']]['score_start_of_year'] += data['score'] if 'score' in data else data['rating']
                    aggregate_result[data['problem_id']]['count_response_start_of_year'] += 1
                else:
                    aggregate_result[data['problem_id']]['course_id_end_of_year'] = data['course_id']
                    aggregate_result[data['problem_id']]['usage_key_end_of_year'] = data['usage_id']
                    aggregate_result[data['problem_id']]['score_end_of_year'] += data['score'] if 'score' in data else data['rating']
                    aggregate_result[data['problem_id']]['count_response_end_of_year'] += 1
            else:
                if data['assessment_time'] == "start_of_year":
                    aggregate_result[data['problem_id']]['course_id_start_of_year'] = data['course_id']
                    aggregate_result[data['problem_id']]['usage_key_start_of_year'] = data['usage_id']
                    aggregate_result[data['problem_id']]['score_start_of_year'] += data['score'] if 'score' in data else data['rating']
                    aggregate_result[data['problem_id']]['count_response_start_of_year'] += 1
                else:
                    aggregate_result[data['problem_id']]['course_id_end_of_year'] = data['course_id']
                    aggregate_result[data['problem_id']]['usage_key_end_of_year'] = data['usage_id']
                    aggregate_result[data['problem_id']]['score_end_of_year'] += data['score'] if 'score' in data else data['rating']
                    aggregate_result[data['problem_id']]['count_response_end_of_year'] += 1

        return aggregate_result

    def get_single_assessment_response(self, raw_data, response):
        """
        update response for single assessment for every student in a class under the
        ``problem_location`` root.
        Arguments:
            raw_data (list): data get from UserResponse OR UserRating models.
            response(dict): 
        Returns:
                [Dict]: Returns a dictionaries
                containing the students updated response.
        """
        for data in raw_data:
            if data['assessment_time'] == "start_of_year":
                response['availaible_respones'] += 1
                if 'student_response' in data:
                    response['student_response']['user_'+str(data['user'])]['response_start_of_year'] = json.loads(data['student_response'])
                    response['student_response']['user_'+str(data['user'])]['score_start_of_year'] = data['score']
                else:
                    response['student_response']['user_'+str(data['user'])]['score_start_of_year'] = data['rating']
            else:
                response['availaible_respones'] += 1
                if 'student_response' in data:
                    response['student_response']['user_'+str(data['user'])]['response_end_of_year'] = json.loads(data['student_response'])
                    response['student_response']['user_'+str(data['user'])]['score_end_of_year'] = data['score']
                else:
                    response['student_response']['user_'+str(data['user'])]['score_end_of_year'] = data['rating']

        return response

    