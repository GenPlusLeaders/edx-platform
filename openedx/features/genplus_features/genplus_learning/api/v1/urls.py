"""
URLs for genplus learning API v1.
"""
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    YearGroupViewSet
)

yeargroup_viewset_router = DefaultRouter()
yeargroup_viewset_router.register('lessons', YearGroupViewSet, basename='lessons')


app_name = 'genplus_learning_api_v1'

urlpatterns = [
    path('', include(yeargroup_viewset_router.urls)),
]
