from django.core.cache import cache
from django.db.models import Q

from common.djangoapps.student.roles import GlobalStaff
from .roles import ProgramInstructorRole, ProgramStaffRole
from .models import Program

ROLES = {
    'instructor': ProgramInstructorRole,
    'staff': ProgramStaffRole,
}
COURSE_PROGRAM_CACHE_KEY = 'course-program-cache-key'


def allow_access(program, level, users):
    change_access(program, level, 'allow', users)


def revoke_access(program, level, users):
    change_access(program, level, 'revoke', users)


def change_access(program, level, action, users):
    try:
        role = ROLES[level](program)
    except KeyError:
        raise ValueError(f"unrecognized level '{level}'")  # lint-amnesty, pylint: disable=raise-missing-from

    if action == 'allow':
        role.add_users(users)
    elif action == 'revoke':
        role.remove_users(users)
    else:
        raise ValueError(f"unrecognized action '{action}'")


def check_course_program(course_key):
    """
    This utils checks if course is part of any program and returns the program instance
    Also it caches the program instance
    """
    course_key_str = str(course_key)
    cache_key = f'{COURSE_PROGRAM_CACHE_KEY}-{str(course_key)}'
    program = cache.get(cache_key)
    if program:
        return program

    programs = Program.objects.filter(Q(intro_unit=course_key) | Q(outro_unit=course_key) | Q(units__course=course_key)).distinct()
    if programs.count() == 1:
        program = programs.first()
        cache.set(key=cache_key, value=program, timeout=None)

    return program


def administrative_accesses_to_program_for_user(user, program):
    """
    Returns types of access a user have for given course.
    """
    global_staff = GlobalStaff().has_user(user)
    staff_access = ProgramStaffRole(program).has_user(user)
    instructor_access = ProgramInstructorRole(program).has_user(user)

    return global_staff, staff_access, instructor_access
