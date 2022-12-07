from django.contrib.auth.models import User
from collections import defaultdict
from openedx.core.lib.cache_utils import get_cache

from common.djangoapps.student.roles import AccessRole
from .models import Program, ProgramAccessRole


class BulkRoleCache:  # lint-amnesty, pylint: disable=missing-class-docstring
    CACHE_NAMESPACE = "genplus.roles.BulkRoleCache"
    CACHE_KEY = 'program_roles_by_user'

    @classmethod
    def prefetch(cls, users):  # lint-amnesty, pylint: disable=missing-function-docstring
        roles_by_user = defaultdict(set)
        get_cache(cls.CACHE_NAMESPACE)[cls.CACHE_KEY] = roles_by_user

        for role in ProgramAccessRole.objects.filter(user__in=users).select_related('user'):
            roles_by_user[role.user.id].add(role)

        users_without_roles = [u for u in users if u.id not in roles_by_user]
        for user in users_without_roles:
            roles_by_user[user.id] = set()

    @classmethod
    def get_user_roles(cls, user):
        return get_cache(cls.CACHE_NAMESPACE)[cls.CACHE_KEY][user.id]


class ProgramRoleCache:
    """
    A cache of the ProgramAccessRoles held by a particular user
    """
    def __init__(self, user):
        try:
            self._program_roles = BulkRoleCache.get_user_roles(user)
        except KeyError:
            self._program_roles = set(
                ProgramAccessRole.objects.filter(user=user).all()
            )

    def has_role(self, role, program):
        """
        Return whether this ProgramRoleCache contains a role with the specified role, program_id
        """
        return any(
            access_role.role == role and
            access_role.program == program
            for access_role in self._program_roles
        )


class ProgramRole(AccessRole):
    def __init__(self, role_name, program: Program):
        super().__init__()
        self.program = program
        self._role_name = role_name

    def has_user(self, user, check_user_activation=True):
        if check_user_activation and not (user.is_authenticated and user.is_active):
            return False

        if not hasattr(user, '_program_roles'):
            # Cache a list of tuples identifying the particular roles that a user has
            # Stored as tuples, rather than django models, to make it cheaper to construct objects for comparison
            user._program_roles = ProgramRoleCache(user)

        return user._program_roles.has_role(self._role_name, self.program)

    def add_users(self, users):
        for user in users:
            if user.is_authenticated and user.is_active and not self.has_user(user):
                entry = ProgramAccessRole(user=user, role=self._role_name, program=self.program)
                entry.save()
                if hasattr(user, '_program_roles'):
                    del user._program_roles

    def remove_users(self, *users):
        entries = ProgramAccessRole.objects.filter(
            user__in=users, role=self._role_name, program=self.program
        )
        entries.delete()
        for user in users:
            if hasattr(user, '_program_roles'):
                del user._program_roles

    def users_with_role(self):
        entries = User.objects.filter(
            programaccessrole__role=self._role_name,
            programaccessrole__program=self.program
        )
        return entries



class ProgramStaffRole(ProgramRole):
    """A Staff member of all courses in a Program"""
    ROLE_NAME = 'staff'

    def __init__(self, *args, **kwargs):
        super().__init__(self.ROLE_NAME, *args, **kwargs)


class ProgramInstructorRole(ProgramRole):
    """Instructor of all courses in a Program"""
    ROLE_NAME = 'instructor'

    def __init__(self, *args, **kwargs):
        super().__init__(self.ROLE_NAME, *args, **kwargs)
