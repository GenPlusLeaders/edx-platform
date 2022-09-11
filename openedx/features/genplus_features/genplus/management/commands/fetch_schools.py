from django.core.management.base import BaseCommand, CommandError
from openedx.features.genplus_features.genplus.rmunify import RmUnify

from openedx.features.genplus_features.genplus.models import School

class Command(BaseCommand):
    help = 'Fetch Schools from RmUnify'

    def handle(self, *args, **options):
        rm_unify = RmUnify()
        schools = rm_unify.fetch(RmUnify.ORGANISATION)
        for school in schools:
            School.objects.update_or_create(
                name=school['DisplayName'], external_id=school['ExternalId'],
                defaults={"guid": school['OrganisationGuid']}
            )
            self.stdout.write(self.style.SUCCESS('Successfully fetched "%s"' % school['DisplayName']))
