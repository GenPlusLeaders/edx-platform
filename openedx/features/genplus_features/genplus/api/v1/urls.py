"""
URLs for genplus core API v1.
"""
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    UserInfo,
    CharacterViewSet,
    ClassViewSet
)

app_name = 'genplus_api_v1'

router = DefaultRouter()
router.register('characters', CharacterViewSet, basename='characters')
router.register('classes', ClassViewSet, basename='classes')

urlpatterns = [
    url(r'^userinfo/$', UserInfo.as_view()),
    url(r'^characters/select/(?P<pk>\d+)/$', CharacterViewSet.as_view({"put": "select_character"})),
    url(r'^classes/add_class/(?P<group_id>\w+)/$', ClassViewSet.as_view({"put": "add_my_class"})),
    path('', include(router.urls)),
]
