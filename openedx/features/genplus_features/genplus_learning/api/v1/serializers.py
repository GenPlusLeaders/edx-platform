from rest_framework import serializers
from openedx.features.genplus_features.genplus_learning.models import YearGroup, Unit


class UnitSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(max_length=32)
    short_description = serializers.CharField(max_length=256)
    course_image_url = serializers.URLField(max_length=128)
    is_locked = serializers.BooleanField(required=True)
    lms_url = serializers.URLField(max_length=128)

    class Meta:
        model = Unit
        fields = ('course_key', 'display_name', 'short_description',
                'course_image_url', 'is_locked', 'lms_url')


class YearGroupSerializer(serializers.ModelSerializer):
    units = UnitSerializer(read_only=True, many=True)

    class Meta:
        model = YearGroup
        fields = ('name', 'year_of_programme', 'units')
