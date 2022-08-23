"""
URLs for genplus learning API v1.
"""
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProgramViewSet,
    ClassStudentViewSet,
)

router = DefaultRouter()
router.register('lessons', ProgramViewSet, basename='lessons')
router.register('class-students', ClassStudentViewSet, basename='class-students')


app_name = 'genplus_learning_api_v1'

urlpatterns = [
    url(r'^lessons/unlock/(?P<pk>\d+)/$', ProgramViewSet.as_view({"put": "unlock_lesson"})),
    path('', include(router.urls)),
]
