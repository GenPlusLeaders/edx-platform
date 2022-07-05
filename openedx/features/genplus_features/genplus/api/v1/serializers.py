from django.conf import settings
from django.middleware import csrf
from rest_framework import serializers
from openedx.features.genplus_features.genplus.models import Character, Skill, Class
from openedx.features.genplus_features.genplus.display_messages import ErrorMessages
from django.contrib.auth import get_user_model


class UserInfoSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='profile.name')
    role = serializers.CharField(source='gen_user.role')
    school = serializers.CharField(source='gen_user.school.name')
    csrf_token = serializers.SerializerMethodField('get_csrf_token')

    def to_representation(self, instance):
        ret = super(UserInfoSerializer, self).to_representation(instance)
        request = self.context.get('request')
        gen_user = self.context.get('gen_user')
        if instance.gen_user.is_student:
            ret['student'] = {
                'on_board': gen_user.student.onboarded,
                'character_id': gen_user.student.character.id
                if gen_user.student.character else None,
                'profile_image': request.build_absolute_uri(
                    gen_user.student.character.profile_pic.url)
                if gen_user.student.character else None
            }
        ret['teacher'] = {
            'profile_image': request.build_absolute_uri(
                gen_user.teacher.profile_image.url)
            if gen_user.teacher.profile_image else None
        }
        return ret

    def get_csrf_token(self, instance):
        return csrf.get_token(self.context.get('request'))

    class Meta:
        model = get_user_model()
        fields = ('id', 'name', 'username', 'csrf_token', 'role',
                  'first_name', 'last_name', 'email', 'school')


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('name',)


class CharacterSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(read_only=True, many=True)

    class Meta:
        model = Character
        fields = '__all__'


class ClassSerializer(serializers.ModelSerializer):
    current_unit = serializers.SerializerMethodField('get_current_unit')
    lesson = serializers.SerializerMethodField('get_lesson')

    def get_current_unit(self, instance):
        return 'Current Unit'

    def get_lesson(self, instance):
        return 'Lesson'

    class Meta:
        model = Class
        fields = ('group_id', 'name', 'current_unit', 'lesson')


class FavoriteClassSerializer(serializers.Serializer):
    action = serializers.CharField(max_length=32)

    def validate(self, data):
        if data['action'] not in ['add', 'remove']:
            raise serializers.ValidationError(
                ErrorMessages.ACTION_VALIDATION_ERROR
            )
        return data
