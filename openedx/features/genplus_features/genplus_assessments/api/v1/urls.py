"""
URLs for genplus badges API v1.
"""
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    StudentAnswersView, ClassFilterViewSet
)

app_name = 'genplus_learning_api_v1'

urlpatterns = [
    url(r'^all-students-responses/(?P<class_id>\w+)/$', StudentAnswersView.as_view({'get': 'all_students_problem_response'}), name='all-students-response-view'),
    url(r'^student-responses/(?P<class_id>\w+)/$', StudentAnswersView.as_view({'get': 'student_problem_response'}), name='student-answer-view'),
    url(r'^genz-filters/(?P<class_id>\w+)/$', ClassFilterViewSet.as_view())
]
