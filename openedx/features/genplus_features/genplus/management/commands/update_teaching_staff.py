from django.core.management import BaseCommand

from openedx.features.genplus_features.genplus.constants import SchoolTypes
from openedx.features.genplus_features.genplus.models import School, GenUser
from openedx.features.genplus_features.genplus.rmunify import RmUnify


class Command(BaseCommand):
    help = 'Update teaching staff organisation id'

    def handle(self, *args, **options):
        rm_unify = RmUnify()
        school_ids = School.objects.filter(type=SchoolTypes.RM_UNIFY).values_list('guid', flat=True)
        for school_id in school_ids:
            teachers = rm_unify.fetch_teachers(school_id)
            for teacher in teachers:
                email = teacher.get('UnifyEmailAddress')
                identity_guid = teacher.get('IdentityGuid')
                GenUser.objects.filter(email=email).update(
                    identity_guid=identity_guid,
                    school_id=school_id
                )
