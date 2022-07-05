from openedx.features.genplus_features.genplus.models import GenUser, Character, Class, Teacher, Student


class GenzMixin:
    @property
    def gen_user(self):
        return self.request.user.gen_user

    @property
    def student(self):
        return Student.objects.get(gen_user=self.gen_user)

    @property
    def teacher(self):
        return Teacher.objects.get(gen_user=self.gen_user)

    @property
    def school(self):
        return self.gen_user.school
