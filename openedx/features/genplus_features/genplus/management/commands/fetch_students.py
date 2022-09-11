from django.core.management.base import BaseCommand, CommandError
from openedx.features.genplus_features.genplus.rmunify import RmUnify
from django.conf import settings
from openedx.features.genplus_features.genplus.models import Class, TempUser, GenUser
from openedx.features.genplus_features.genplus.constants import GenUserRoles
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Fetch class students from RmUnify'

    def handle(self, *args, **options):
        rm_unify = RmUnify()
        schools = rm_unify.fetch(RmUnify.ORGANISATION)
        for gen_class in Class.objects.filter(is_visible=True):
            url = RmUnify.TEACHING_GROUP.format(RmUnify.ORGANISATION, gen_class.school.guid)
            url = f"{url}/{gen_class.group_id}"
            data = rm_unify.fetch(url)
            try:
                for student in data['Students']:
                    try:
                        print(student['UserName'], student['UnifyEmailAddress'])
                        User.objects.get(username=student['UserName'], email=['UnifyEmailAddress'])
                    except User.DoesNotExist:
                        temp_user = TempUser.objects.get_or_create(username=student['UserName'], email=student['UnifyEmailAddress'])
                        gen_user = GenUser.objects.update_or_create(
                                    role=GenUserRoles.STUDENT,
                                    school=gen_class.school,
                                    defaults={'temp_user': temp_user[0]})
                        gen_class.students.add(gen_user[0].student)

            except KeyError:
                self.stdout.write(self.style.ERROR('An Error occur'))
