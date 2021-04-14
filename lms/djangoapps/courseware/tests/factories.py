# Factories are self documenting  # lint-amnesty, pylint: disable=missing-module-docstring


import json
from functools import partial

import factory
from factory.django import DjangoModelFactory
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator

from lms.djangoapps.courseware.models import (
    StudentModule,
    XModuleStudentInfoField,
    XModuleStudentPrefsField,
    XModuleUserStateSummaryField
)
from common.djangoapps.student.tests.factories import UserFactory

COURSE_KEY = CourseKey.from_string('edX/test_course/test')
LOCATION = partial(COURSE_KEY.make_usage_key, 'problem')


class StudentModuleFactory(DjangoModelFactory):  # lint-amnesty, pylint: disable=missing-class-docstring
    class Meta:
        model = StudentModule

    module_type = "problem"
    student = factory.SubFactory(UserFactory)
    course_id = CourseLocator("MITx", "999", "Robot_Super_Course")
    state = None
    grade = None
    max_grade = None
    done = 'na'


class UserStateSummaryFactory(DjangoModelFactory):  # lint-amnesty, pylint: disable=missing-class-docstring
    class Meta:
        model = XModuleUserStateSummaryField

    field_name = 'existing_field'
    value = json.dumps('old_value')
    usage_id = LOCATION('usage_id')


class StudentPrefsFactory(DjangoModelFactory):  # lint-amnesty, pylint: disable=missing-class-docstring
    class Meta:
        model = XModuleStudentPrefsField

    field_name = 'existing_field'
    value = json.dumps('old_value')
    student = factory.SubFactory(UserFactory)
    module_type = 'mock_problem'


class StudentInfoFactory(DjangoModelFactory):  # lint-amnesty, pylint: disable=missing-class-docstring
    class Meta:
        model = XModuleStudentInfoField

    field_name = 'existing_field'
    value = json.dumps('old_value')
    student = factory.SubFactory(UserFactory)
