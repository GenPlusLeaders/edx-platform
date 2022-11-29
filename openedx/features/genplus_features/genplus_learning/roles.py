from xmodule.modulestore.django import modulestore

from common.djangoapps.student.roles import AccessRole
from lms.djangoapps.instructor.access import allow_access, revoke_access
from .models import Program


class ProgramAccessRole(AccessRole):
    def __init__(self, role_name, program: Program):
        super().__init__()
        self.program = program
        self._role_name = role_name

    def has_user(self, gen_user):
        pass

    def add_users(self, *gen_users, send_email):
        courses = []
        if self.program.intro_unit:
            courses.append(self.program.intro_unit)
        if self.program.outro_unit:
            courses.append(self.program.outro_unit)
        courses += [unit.course for unit in self.program.units.all()]

        for course in courses:
            for gen_user in gen_users:
                allow_access(course, gen_user.user, self._role_name, send_email)

    def remove_users(self, *gen_users, send_email):
        courses = []
        if self.program.intro_unit:
            courses.append(self.program.intro_unit)
        if self.program.outro_unit:
            courses.append(self.program.outro_unit)
        courses += [unit.course for unit in self.program.units.all()]

        for course in courses:
            for gen_user in gen_users:
                revoke_access(course, gen_user.user, self._role_name, send_email)


    def users_with_role(self):
        pass


class ProgramStaffRole(ProgramAccessRole):
    """A Staff member of all courses in a Program"""
    ROLE_NAME = 'staff'

    def __init__(self, *args, **kwargs):
        super().__init__(self.ROLE_NAME, *args, **kwargs)


class ProgramInstructorRole(ProgramAccessRole):
    """Instructor of all courses in a Program"""
    ROLE_NAME = 'instructor'

    def __init__(self, *args, **kwargs):
        super().__init__(self.ROLE_NAME, *args, **kwargs)
