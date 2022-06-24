from rest_framework import serializers
from openedx.features.genplus_features.genplus.models import (Character, Teacher,
                                                              School, GenUser, Student)
from openedx.features.genplus_features.genplus_learning.models import Skill
from django.contrib.auth.models import User


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('name', )


class CharacterSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(read_only=True, many=True)

    class Meta:
        model = Character
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ('name',)


class GenUserSerializer(serializers.ModelSerializer):
    school = SchoolSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = GenUser
        fields = ('school', 'user',)


class TeacherProfileSerializer(serializers.ModelSerializer):
    gen_user = GenUserSerializer(read_only=True)

    class Meta:
        model = Teacher
        read_only_fields = ('gen_user',)
        fields = ('gen_user', 'profile_image',)


class StudentProfileSerializer(serializers.ModelSerializer):
    gen_user = GenUserSerializer(read_only=True)
    character = serializers.PrimaryKeyRelatedField(queryset=Character.objects.all())

    class Meta:
        model = Student
        read_only_fields = ("gen_user",)
        fields = ('gen_user', 'character',)
        
    def update(self, instance, validated_data):
        instance.character = validated_data.pop('character')
        instance.save()
        return instance