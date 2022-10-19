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
    url(r'^student-answers/(?P<class_id>\w+)/$', StudentAnswersView.as_view({'get': 'list'}), name='student-answer-view'),
    url(r'^genz-filters/(?P<class_id>\w+)/$', ClassFilterViewSet.as_view())
]
