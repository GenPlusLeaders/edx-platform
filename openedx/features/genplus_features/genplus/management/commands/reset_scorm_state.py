import logging

from django.core.management import BaseCommand

from lms.djangoapps.courseware.models import StudentModule
from openedx.features.genplus_features.genplus.constants import GenUserRoles
from openedx.features.genplus_features.genplus.models import GenUser

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        teachers = list(GenUser.objects.filter(role__in=GenUserRoles.TEACHING_ROLES).values_list('user', flat=True))

        module_to_reset = StudentModule.objects.filter(
            student_id__in=teachers,
            module_type='scormxblock'
        )

        logger.info(
            f'clearing {module_to_reset.count()} scormxblock states for these ({", ".join(GenUserRoles.TEACHING_ROLES)}) roles'
        )
        module_to_reset.delete()
        logger.info('Done!!!')
