from django.core.management.base import BaseCommand, CommandError

from openedx.features.genplus_features.genplus.exceptions import XporterException
from openedx.features.genplus_features.genplus.models import School, Class
from openedx.features.genplus_features.genplus.xporter import Xporter
from openedx.features.genplus_features.genplus.constants import ClassTypes, SchoolTypes


class Command(BaseCommand):
    help = 'Fetch students against each visible Xporter class.'

    def handle(self, *args, **options):
        for gen_class in Class.objects.filter(school__type=SchoolTypes.XPORTER, is_visible=True):
            try:
                self.stdout.write(self.style.WARNING(f'Fetching students for {gen_class.name}'))
                xporter = Xporter(gen_class.school.guid)
                xporter.fetch_students(gen_class.id)
            except XporterException:
                self.stdout.write(self.style.ERROR(f'Error fetching classes for {gen_class.name}'))
                continue
        self.stdout.write(self.style.SUCCESS('Successfully fetched classes'))
