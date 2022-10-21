import logging
import json
from lxml import etree
from xmodule.modulestore.django import modulestore
from rest_framework import views, viewsets
from opaque_keys.edx.keys import UsageKey, CourseKey
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from collections import defaultdict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse


from lms.djangoapps.courseware.models import StudentModule
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.courseware.user_state_client import DjangoXBlockUserStateClient
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import Class
from openedx.features.genplus_features.genplus.api.v1.permissions import IsTeacher
from .serializers import ClassSerializer


log = logging.getLogger(__name__)


class StudentAnswersView(viewsets.ViewSet):
    
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]

    def students_problem_response(self, request, **kwargs):
        class_id = kwargs.get('class_id', None)
        student_id = request.GET.get('student_id',None)
        students = []
        if student_id == "all":
            students = list(Class.objects.prefetch_related('students').get(pk=class_id).students.values_list('gen_user__user_id',flat=True))
        else:
            students.append(student_id)
        course_id = request.GET.get('course_id',None)
        course_keys = CourseKey.from_string(course_id)
        problem_locations = request.GET.get('problem_locations',None)
        filter = request.GET.get('filter',None)

        response = self.build_students_result(
            user_id = self.request.user.id,
            course_key = course_keys,
            usage_key_str = problem_locations,
            student_list = students,
            filter = filter,
        )

        print(response)
        return Response(response)
    
    def build_students_result(self,user_id, course_key, usage_key_str, student_list, filter):
        """
        Generate a result for problem responses for all problem under the
        ``problem_location`` root.
        Arguments:
            user_id (int): The user id for the user generating the report
            course_key (CourseKey): The ``CourseKey`` for the course whose report
                is being generated
            usage_key_str: The generated report will include these
                blocks and their child blocks.
            filter_types (List[str]): The report generator will only include data for
                block types in this list.
        Returns:
              List[Dict]: Returns a list of dictionaries
                containing the student aggregate result data.
        """
        usage_keys = [UsageKey.from_string(usage_key_str).map_into_course(course_key)]
        user = get_user_model().objects.get(pk=user_id)

        student_data = []
        max_count = settings.FEATURES.get('MAX_PROBLEM_RESPONSES_COUNT')

        store = modulestore()
        user_state_client = DjangoXBlockUserStateClient()

        with store.bulk_operations(course_key):
            for usage_key in usage_keys:  # lint-amnesty, pylint: disable=too-many-nested-blocks
                if max_count is not None and max_count <= 0:
                    break
                course_blocks = get_course_blocks(user, usage_key)
                for title, path, block_key in self.build_problem_list(course_blocks, usage_key):
                    # Chapter and sequential blocks are filtered out since they include state
                    # which isn't useful for this report.
                    if block_key.block_type in ('sequential', 'chapter'):
                        continue

                    block = store.get_item(block_key)
                    generated_report_data = defaultdict(list)

                    # Blocks can implement the generate_report_data method to provide their own
                    # human-readable formatting for user state.
                    if hasattr(block, 'generate_report_data'):
                        try:
                            user_state_iterator = user_state_client.iter_all_for_block(block_key)
                            for username, state in block.generate_report_data(user_state_iterator, max_count):
                                generated_report_data[username].append(state)
                        except NotImplementedError:
                            pass

                    responses = {}
                    
                    if block_key.block_type in ('problem'):
                        responses = self.get_problem_attributes(store, block_key)
                        responses['results'] = []
                        aggregate_result = {}

                        for user_id in student_list:
                            user = get_user_model().objects.get(pk=user_id)
                            user_states = generated_report_data.get(user.username)
                            if user_states:
                                # For each response in the block, aggregate the result for the problem, and add in the responses
                                if responses['problem_type'] in ('singleChoice', 'multipleChoice'):
                                    if filter == "aggregate_response":
                                        aggregate_result.update(self.students_aggregate_result(user_states, aggregate_result))
                                    elif filter == "individual_response":
                                        responses['results'].append(self.students_multiple_choice_response(user_states, user))
                                else:
                                    responses['results'].append(self.students_short_answer_response(user_states, user))

                        if responses['problem_type'] in ('singleChoice', 'multipleChoice') and filter == "aggregate_response":
                            for key,value in aggregate_result.items():
                                responses['results'].append({
                                    'title': key,
                                    'count': value['count'],
                                    'is_correct': value['is_correct'],
                                }) 
                        student_data.append(responses)

                    if max_count is not None:
                        max_count -= len(responses)
                        if max_count <= 0:
                            break

        return student_data
    
    def students_aggregate_result(self, user_states, aggregate_result):
        """
        Generate aggregate response for problem(Multiple Choices and Single Choices) as per the user state  under the
        ``problem_location`` root.
        Arguments:
            user_State (List): The user id for the user generating the report
            
        Returns:
              [Dict]: Returns a dictionaries
                containing the student aggregate result data.
        """
        for user_state in user_states:
            user_answer = user_state['Answer']
            correct_answer = user_state['Correct Answer']
            if user_state['Answer'] not in aggregate_result:
                aggregate_result[user_state['Answer']] = {}
                aggregate_result[user_state['Answer']]['count'] = 1
                aggregate_result[user_state['Answer']]['is_correct'] = correct_answer == user_answer
            else:
                aggregate_result[user_state['Answer']]['count'] += 1

        return aggregate_result

    def get_problem_attributes(self, store, block_key):
        responses = {}
        responses['problem_key'] = str(block_key)
        responses['problem_id'] = block_key.block_id
        raw_data = store.get_item(block_key).data
        parser = etree.XMLParser(remove_blank_text=True)
        problem = etree.XML(raw_data, parser=parser)
        data_dict = {}
        for e in problem.iter("*"):
            if e.tag == 'problem':
                responses['problem_type'] =  e.attrib.get('class')
            elif e.text and e.attrib.get('class') == 'question-text':
                responses['question_text'] =  e.text
            elif e.text and e.tag == 'choice':
                choice_dict = {}
                choice_dict['statement'] = e.text
                choice_dict['correct'] = e.attrib.get('correct')
                data_dict.update({e.attrib.get('class'): choice_dict})
        if responses['problem_type'] != "shortAnswers":
            responses['problem_choices'] = data_dict
        return responses

    def students_short_answer_response(self, user_states, user):
        """
        Generate response for as per the user state for all short answers under the
        ``problem_location`` root.
        Arguments:
            user_State (List): The user id for the user generating the report
            
        Returns:
              [Dict]: Returns a dictionaries
                containing the student aggregate result data.
        """
        student_response_dict = {}
        for user_state in user_states:
            user_answer = user_state['Answer']
            user_question = user_state['Question']
            student_response_dict = {
                'username': user.username,
                'full_name': user.get_full_name(),
                'question': user_question,
                'answer': user_answer,
            }
        
        return student_response_dict

    def students_multiple_choice_response(self, user_states, user):
        """
        Generate response for as per the user state for all for problem(Multiple Choices and Single Choices) under the
        ``problem_location`` root.
        Arguments:
            user_State (List): The user id for the user generating the report
            
        Returns:
              [Dict]: Returns a dictionaries
                containing the student aggregate result data.
        """
        student_response_dict = {}
        for user_state in user_states:
            user_answer = user_state['Answer']
            correct_answer = user_state['Correct Answer']
            user_answer_list = list(user_answer.split(","))
            correct_answer_list = list(correct_answer.split(","))
            student_response_dict = {
                'username': user.username,
                'full_name': user.get_full_name(),
                'answer': user_answer,
                'correct_answer': correct_answer,
                'earned_score': len(list(set(correct_answer_list).intersection(set(user_answer_list)))),
                'total_score': len(correct_answer_list),
            }
        
        return student_response_dict      

    def list_problem_responses(self, course_key, problem_location, student_list, limit_responses=None):
        """
        Return responses to a given problem as a dict.

        list_problem_responses(course_key, problem_location)

        would return [
            {'username': u'user1', 'state': u'...'},
            {'username': u'user2', 'state': u'...'},
            {'username': u'user3', 'state': u'...'},
        ]

        where `state` represents a student's response to the problem
        identified by `problem_location`.
        """
        if isinstance(problem_location, UsageKey):
            problem_key = problem_location
        else:
            problem_key = UsageKey.from_string(problem_location)
        # Are we dealing with an "old-style" problem location?
        run = problem_key.run
        if not run:
            problem_key = UsageKey.from_string(problem_location).map_into_course(course_key)
        if problem_key.course_key != course_key:
            return []

        smdat = StudentModule.objects.filter(
            course_id=course_key,
            module_state_key=problem_key,
            student_id__in = student_list
        )
        smdat = smdat.order_by('student')
        if limit_responses is not None:
            smdat = smdat[:limit_responses]

        return [
        {'username': response.student.username, 'state': self.get_response_state(response)}
        for response in smdat
    ]
    
    def build_problem_list(self, course_blocks, root, path=None):
        """
        Generate a tuple of display names, block location paths and block keys
        for all problem blocks under the ``root`` block.
        Arguments:
            course_blocks (BlockStructureBlockData): Block structure for a course.
            root (UsageKey): This block and its children will be used to generate
                the problem list
            path (List[str]): The list of display names for the parent of root block
        Yields:
            Tuple[str, List[str], UsageKey]: tuple of a block's display name, path, and
                usage key
        """
        name = course_blocks.get_xblock_field(root, 'display_name') or root.block_type
        if path is None:
            path = [name]

        yield name, path, root

        for block in course_blocks.get_children(root):
            name = course_blocks.get_xblock_field(block, 'display_name') or block.block_type
            yield from self.build_problem_list(course_blocks, block, path + [name])


    def get_response_state(self, response):
        """
        Returns state of a particular response as string.

        This method also does necessary encoding for displaying unicode data correctly.
        """
        def get_transformer():
            """
            Returns state transformer depending upon the problem type.
            """
            problem_state_transformers = {
                'openassessment': self.transform_ora_state,
                'problem': self.transform_capa_state
            }
            problem_type = response.module_type
            return problem_state_transformers.get(problem_type)

        problem_state = response.state
        problem_state_transformer = get_transformer()
        if not problem_state_transformer:
            return problem_state

        state = json.loads(problem_state)
        try:
            transformed_state = problem_state_transformer(state)
            return json.dumps(transformed_state, ensure_ascii=False)
        except TypeError:
            username = response.student.username
            err_msg = (
                'Error occurred while attempting to load learner state '
                '{username} for state {state}.'.format(
                    username=username,
                    state=problem_state
                )
            )
            log.error(err_msg)
            return problem_state
    
    def transform_ora_state(self,state):
        """
        ORA problem state transformer transforms the problem states.

        Some state variables values are json dumped strings which needs to be loaded
        into a python object.
        """
        fields_to_transform = ['saved_response', 'saved_files_descriptions']

        for field in fields_to_transform:
            field_state = state.get(field)
            if not field_state:
                continue

            state[field] = json.loads(field_state)
        return state


    def transform_capa_state(self,state):
        """
        Transforms the CAPA problem state.
        """
        return state

class ClassFilterViewSet(views.APIView):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ClassSerializer

    def get(self,request, **kwargs):
        class_id = kwargs.get('class_id', None)
        try:
            gen_class = Class.objects.get(pk=class_id)
            data = ClassSerializer(gen_class).data
        except Class.DoesNotExist:
            return Class.objects.none()
        return Response(data)


