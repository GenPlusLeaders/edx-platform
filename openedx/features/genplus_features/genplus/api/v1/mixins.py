class GenzMixin:
    @property
    def gen_user(self):
        return self.request.user.gen_user

    @property
    def school(self):
        return self.gen_user.school
