from rest_framework import serializers
from common.djangoapps.student.models import UserProfile
from openedx.features.genplus_features.genplus.models import Teacher, Character, Skill, Class, JournalPost, EmailRecord
from openedx.features.genplus_features.common.display_messages import ErrorMessages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.hashers import check_password


class UserInfoSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    role = serializers.CharField(source='gen_user.role')
    school = serializers.CharField(source='gen_user.school.name')
    school_type = serializers.CharField(source='gen_user.school.type')
    is_school_active = serializers.BooleanField(source='gen_user.school.is_active')
    csrf_token = serializers.SerializerMethodField('get_csrf_token')
    has_changed_password = serializers.SerializerMethodField('get_password_changed')

    def get_name(self, instance):
        name = ''
        if instance.profile and (instance.profile.name or '').strip():
            name = instance.profile.name
        elif (instance.first_name or '').strip() or (instance.last_name or '').strip():
            name = f'{instance.first_name} {instance.last_name}'.strip()
        return name

    def to_representation(self, instance):
        user_info = super(UserInfoSerializer, self).to_representation(instance)
        request = self.context.get('request')
        gen_user = self.context.get('gen_user')
        if instance.gen_user.is_student:
            student_profile = {
                'on_board': gen_user.student.onboarded,
                'has_access_to_lessons': gen_user.student.has_access_to_lessons,
                'character_id': gen_user.student.character.id
                if gen_user.student.character else None,
                'class_id': gen_user.student.active_class.id
                if gen_user.student.active_class else None,
                'profile_image': request.build_absolute_uri(
                    gen_user.student.character.profile_pic.url)
                if gen_user.student.character else None,
            }

            user_info.update(student_profile)
        elif instance.gen_user.is_teacher:
            teacher_profile = {
                'on_board': '',
                'character_id': '',
                'profile_image': request.build_absolute_uri(
                    gen_user.teacher.profile_image.url)
                if gen_user.teacher.profile_image else None
            }

            user_info.update(teacher_profile)
        return user_info

    def get_csrf_token(self, instance):
        return self.context.get('request').COOKIES.get('csrftoken')

    def get_password_changed(self, instance):
        if instance.gen_user.from_private_school:
            return instance.gen_user.has_password_changed
        return True

    class Meta:
        model = get_user_model()
        fields = ('id', 'name', 'username', 'csrf_token', 'role',
                  'first_name', 'last_name', 'email', 'school', 'school_type', 'is_school_active', 'has_changed_password')


class TeacherSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = ('id', 'user_id', 'name', 'profile_image')

    def get_user_id(self, obj):
        return obj.gen_user.user.id

    def get_name(self, instance):
        name = ''
        if instance.profile and (instance.profile.name or '').strip():
            name = instance.profile.name
        elif (instance.first_name or '').strip() or (instance.last_name or '').strip():
            name = f'{instance.first_name} {instance.last_name}'.strip()
        return name


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

    def lastest_unlocked_unit(self, gen_class):
        # Returns: Latest unlocked unit
        reversed_class_units = gen_class.class_units.all().reverse()

        for class_unit in reversed_class_units:
            if not class_unit.is_locked:
                return class_unit
        return None

    def get_current_unit(self, instance):
        current_unit = self.lastest_unlocked_unit(instance)

        if current_unit:
            return current_unit.unit.course.display_name
        return 'Not Available'

    def get_lesson(self, instance):
        current_unit = self.lastest_unlocked_unit(instance)
        if current_unit:
            current_lesson = current_unit.class_lessons.filter(is_locked=False).last()
            return current_lesson.display_name
        return 'Not Available'

    class Meta:
        model = Class
        fields = ('id', 'name', 'group_id', 'current_unit', 'lesson')


class ClassSummarySerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name")
    program_name = serializers.CharField(source="program.year_group.name", default=None)
    program_id = serializers.IntegerField(source="program.id", default=None)
    year_group_id = serializers.IntegerField(source="program.year_group.id", default=None)

    class Meta:
        model = Class
        fields = (
            'group_id',
            'name',
            'school_name',
            'program_name',
            'program_id',
            'year_group_id',
        )


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
        fields = ('id', 'title', 'skill', 'description', 'teacher', 'journal_type', 'is_editable', 'modified')


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
    is_force_change = serializers.BooleanField(default=False)

    set_password_form_class = SetPasswordForm

    def __init__(self, *args, **kwargs):
        super(ChangePasswordSerializer, self).__init__(*args, **kwargs)
        self.request = self.context.get('request')
        self.is_force_change = self.context.get('is_force_change')
        self.user = getattr(self.request, 'user', None)
        # check if force change then remove old_password field
        if self.is_force_change:
            self.fields.pop('old_password')

    def validate_old_password(self, value):
        invalid_password_conditions = (
            self.is_force_change,
            self.user,
            not self.user.check_password(value)
        )

        if all(invalid_password_conditions):
            raise serializers.ValidationError(ErrorMessages.OLD_PASSWORD_ERROR)
        return value

    def validate_new_password1(self, value):
        # check if new password is not same as the old one
        if check_password(value, self.user.password):
            raise serializers.ValidationError(ErrorMessages.NEW_SAME_AS_OLD_PASSWORD_ERROR)
        return value



    def validate(self, attrs):
        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs
        )
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)
        return attrs

    def save(self):
        self.set_password_form.save()
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(self.request, self.user)


class ChangePasswordByTeacherSerializer(serializers.Serializer):
    students = serializers.ListField(required=True, child=serializers.IntegerField())
    password = serializers.CharField(required=True)


class ContactSerailizer(serializers.ModelSerializer):
    class Meta:
        model = EmailRecord
        fields = ('from_email', 'to_email', 'subject',)
