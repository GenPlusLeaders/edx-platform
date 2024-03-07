from django.core.management.base import BaseCommand, CommandError

from openedx.features.genplus_features.genplus.exceptions import XporterException
from openedx.features.genplus_features.genplus.models import School
from openedx.features.genplus_features.genplus.xporter import Xporter
from openedx.features.genplus_features.genplus.constants import ClassTypes, SchoolTypes


class Command(BaseCommand):
    help = 'Fetch Classes against each Xporter School.'

    def handle(self, *args, **options):
        for school in School.objects.filter(type=SchoolTypes.XPORTER):
            try:
                self.stdout.write(self.style.INFO(f'Fetching classes for {school.name}'))
                xporter = Xporter(school.guid)
                xporter.fetch_classes(ClassTypes.XPORTER_REGISTRATION_GROUP)
                xporter.fetch_classes(ClassTypes.XPORTER_TEACHING_GROUP)
            except XporterException:
                self.stdout.write(self.style.ERROR(f'Error fetching classes for {school.name}'))
                continue
        self.stdout.write(self.style.SUCCESS('Successfully fetched classes'))
