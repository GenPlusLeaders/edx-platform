from rest_framework import serializers
from common.djangoapps.student.models import UserProfile
from openedx.features.genplus_features.genplus.models import GenUserProfile, Character, Skill, Class, JournalPost, EmailRecord
from openedx.features.genplus_features.common.display_messages import ErrorMessages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.forms import SetPasswordForm
from openedx.core.djangoapps.oauth_dispatch.api import destroy_oauth_tokens


class UserInfoSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='profile.name', default=None)
    role = serializers.CharField(source='gen_user.role')
    on_board = serializers.BooleanField(source='gen_user.onboarded')
    character_id = serializers.IntegerField(source='gen_user.character.id', default=None)
    school = serializers.CharField(source='gen_user.school.name')
    school_type = serializers.CharField(source='gen_user.school.type')
    profile_image = serializers.SerializerMethodField()
    csrf_token = serializers.SerializerMethodField()
    has_access_to_lessons = serializers.BooleanField(source='gen_user.has_access_to_lessons')

    def get_profile_image(self, instance):
        request = self.context.get('request')
        gen_user = instance.gen_user
        url = None
        if gen_user.is_student and gen_user.character:
            url = request.build_absolute_uri(gen_user.character.profile_pic.url)
        elif gen_user.is_teacher and gen_user.profile_image:
            url = request.build_absolute_uri(gen_user.profile_image.url)

        return url

    def get_csrf_token(self, instance):
        return self.context.get('request').COOKIES.get('csrftoken')

    class Meta:
        model = get_user_model()
        fields = ('id', 'name', 'username', 'csrf_token', 'role',
                  'first_name', 'last_name', 'email', 'school', 'school_type',
                  'on_board', 'character_id', 'profile_image', 'has_access_to_lessons',)

class TeacherSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='profile.name', default=None)
    profile_image = serializers.SerializerMethodField()
    class Meta:
        model = get_user_model()
        fields = ('id', 'name', 'profile_image')

    def get_profile_image(self, instance):
        gen_user = GenUserProfile.objects.filter(user=instance).first()
        return gen_user.profile_image.url if gen_user else None


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'


class CharacterSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(read_only=True, many=True)

    class Meta:
        model = Character
        fields = '__all__'


class ClassListSerializer(serializers.ModelSerializer):
    current_unit = serializers.SerializerMethodField('get_current_unit')
    lesson = serializers.SerializerMethodField('get_lesson')

    def get_current_unit(self, instance):
        return 'Current Unit'

    def get_lesson(self, instance):
        return 'Lesson'

    class Meta:
        model = Class
        fields = ('id', 'name', 'group_id', 'current_unit', 'lesson')


class ClassSummarySerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name")
    program_name = serializers.CharField(source="program.year_group.name", default=None)

    class Meta:
        model = Class
        fields = ('group_id', 'name', 'school_name', 'program_name',)


class FavoriteClassSerializer(serializers.Serializer):
    action = serializers.CharField(max_length=32)

    def validate(self, data):
        if data['action'] not in ['add', 'remove']:
            raise serializers.ValidationError(
                ErrorMessages.ACTION_VALIDATION_ERROR
            )
        return data


class JournalListSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)
    teacher = TeacherSerializer(read_only=True)
    class Meta:
        model = JournalPost
        fields = ('id', 'title', 'skill', 'description', 'teacher', 'journal_type', 'created')


class StudentPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalPost
        fields = ('student', 'title', 'skill', 'description', 'journal_type')
        extra_kwargs = {'skill': {'required': True, 'allow_null': False}}


class TeacherFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalPost
        fields = ('teacher', 'student', 'title', 'description', 'journal_type')
        extra_kwargs = {'teacher': {'required': True, 'allow_null': False}}


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128)
    new_password1 = serializers.CharField(max_length=128)
    new_password2 = serializers.CharField(max_length=128)

    set_password_form_class = SetPasswordForm

    def __init__(self, *args, **kwargs):
        super(ChangePasswordSerializer, self).__init__(*args, **kwargs)
        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    def validate_old_password(self, value):
        invalid_password_conditions = (
            self.user,
            not self.user.check_password(value)
        )

        if all(invalid_password_conditions):
            raise serializers.ValidationError(ErrorMessages.OLD_PASSWORD_ERROR)
        return value

    def validate(self, attrs):
        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs
        )

        if not self.set_password_form.is_valid():
            print(self.set_password_form.errors)
            raise serializers.ValidationError(self.set_password_form.errors)
        return attrs

    def save(self):
        self.set_password_form.save()
        # delete all oauth token and logout the user
        destroy_oauth_tokens(self.user)
        logout(self.request)


class ChangePasswordByTeacherSerializer(serializers.Serializer):
    students = serializers.ListField(required=True, child=serializers.IntegerField())
    password = serializers.CharField(required=True)


class ContactSerailizer(serializers.ModelSerializer):
    class Meta:
        model = EmailRecord
        fields = ('from_email', 'to_email', 'subject',)
