from openedx.features.genplus_features.genplus.models import (Character, Class,
                                                              GenUser, Student,
                                                              Teacher)


class GenzMixin:
    @property
    def gen_user(self):
        return self.request.user.gen_user

    @property
    def school(self):
        return self.gen_user.school
