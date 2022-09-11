from django.core.management.base import BaseCommand, CommandError
from openedx.features.genplus_features.genplus.rmunify import RmUnify

from openedx.features.genplus_features.genplus.models import School, Class


class Command(BaseCommand):
    help = 'Fetch Classes against each school RmUnify'
    argument_options = ['teachinggroup', 'registration']

    def add_arguments(self, parser):
        parser.add_argument("-f", "--from", type=str)

    def handle(self, *args, **options):
        if options['from'] in self.argument_options:
            rm_unify = RmUnify()
            for school in School.objects.all():
                if options['from'] == 'teachinggroup':
                    url = RmUnify.TEACHING_GROUP.format(RmUnify.ORGANISATION, school.guid)
                else:
                    url = RmUnify.REGISTRATION_GROUP.format(RmUnify.ORGANISATION, school.guid)

                classes = rm_unify.fetch(url)

                for gen_class in classes:
                    Class.objects.update_or_create(
                        school=school,
                        group_id=gen_class['GroupId'],
                        defaults={"name": gen_class['DisplayName']}
                    )
                self.stdout.write(self.style.SUCCESS('Successfully fetched classes for "%s"' % school.name))
