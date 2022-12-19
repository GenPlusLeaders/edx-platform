import re
import logging
from hashlib import sha1
from http import HTTPStatus
from django.conf import settings
import requests
import base64
import hmac
from datetime import datetime
from openedx.features.genplus_features.genplus.models import GenUser, Student, School, Class
from openedx.features.genplus_features.genplus.constants import SchoolTypes, ClassTypes, GenUserRoles
from .constants import RmUnifyUpdateTypes
from django.db.models import Q
import openedx.features.genplus_features.genplus.tasks as genplus_tasks



logger = logging.getLogger(__name__)


class RmUnifyException(BaseException):
    pass


class BaseRmUnify:
    def __init__(self):
        self.key = settings.RM_UNIFY_KEY
        self.secret = settings.RM_UNIFY_SECRET
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def fetch(self, source, source_id=None, provisioning=False):
        headers = self.get_header()
        url = self.generate_url(source, source_id, provisioning=provisioning)
        response = requests.get(url, headers=headers)
        if response.status_code != HTTPStatus.OK.value:
            logger.exception(response.reason)
            return []
        return response.json()

    @property
    def hashed(self):
        hashed = hmac.new(bytes(self.secret, 'utf-8'), bytes(self.timestamp, 'utf-8'), sha1).digest()
        hashed = str(base64.urlsafe_b64encode(hashed), "UTF-8")
        hashed = hashed.replace('-', '+')
        return hashed.replace('_', '/')

    @staticmethod
    def generate_url(source, source_id, provisioning=False):
        url = settings.RM_UNIFY_URL
        if not provisioning:
            url = url + '/graph/'
        if source:
            url = url + source
        if source_id:
            url = url + source_id
        return url

    def get_header(self):
        return {"Authorization": "Unify " + self.key + "_" + self.timestamp + ":" + self.hashed}


class RmUnify(BaseRmUnify):
    ORGANISATION = 'organisation/'
    TEACHING_GROUP = '{}{}/teachinggroup/'
    REGISTRATION_GROUP = '{}{}/registrationgroup/'

    def fetch_schools(self):
        schools = self.fetch(self.ORGANISATION)
        for school in schools:
            obj, created = School.objects.update_or_create(
                name=school['DisplayName'],
                external_id=school['ExternalId'],
                type=SchoolTypes.RM_UNIFY,
                defaults={"guid": school['OrganisationGuid']}
            )
            response = 'created' if created else 'updated'
            logger.info('{} has been {} successfully.'.format(school['DisplayName'], response))

    def fetch_classes(self, class_type, queryset=School.objects.all()):
        for school in queryset:
            fetch_type = re.sub(r'(?<!^)(?=[A-Z])', '_', class_type).upper()
            # get specific url based on class_type
            url = getattr(self, fetch_type)
            classes = self.fetch(url.format(RmUnify.ORGANISATION, school.guid))
            for gen_class in classes:
                Class.objects.update_or_create(
                    type=class_type,
                    school=school,
                    group_id=gen_class['GroupId'],
                    name=gen_class['DisplayName'],
                    defaults={"name": gen_class['DisplayName']}
                )
            logger.info('classes for {} has been successfully fetched.'.format(school.name))

    def fetch_students(self, query=Class.visible_objects.all()):
        for gen_class in query:
            fetch_type = re.sub(r'(?<!^)(?=[A-Z])', '_', gen_class.type).upper()
            # formatting url according to class type
            url = getattr(self, fetch_type).format(RmUnify.ORGANISATION,
                                                   gen_class.school.guid)
            data = self.fetch(f"{url}/{gen_class.group_id}")
            gen_user_ids = []
            for student_data in data['Students']:
                student_email = student_data.get('UnifyEmailAddress')
                identity_guid = student_data.get('IdentityGuid')
                gen_user, created = GenUser.objects.get_or_create(
                    email=student_email,
                    role=GenUserRoles.STUDENT,
                    school=gen_class.school,
                )
                # update the identity_guid
                gen_user.identity_guid = identity_guid
                gen_user.save()
                gen_user_ids.append(gen_user.pk)

            gen_students = Student.objects.filter(gen_user__in=gen_user_ids)
            gen_class.students.add(*gen_students)


class RmUnifyProvisioning(BaseRmUnify):

    UPDATES = '/appprovisioning/v2/{}/updates/'
    DELETE_BATCH = '/appprovisioning/v2/{}/deletebatch/'

    def get_header(self):
        return {"Authorization": "Unify " + self.timestamp + ":" + self.hashed}

    def provision(self):
        data = self.fetch(self.UPDATES.format(self.key), provisioning=True)
        if data:
            updates_batch = []
            # check updates and update/delete user accordingly
            for update in data['Updates']:
                if update['Type'] == RmUnifyUpdateTypes.USER:
                    self.update_user(update['UpdateData'])
                elif update['Type'] == RmUnifyUpdateTypes.DELETE_USER:
                    try:
                        # only deleting if user with unify guid exist in our system
                        identity_guid = update['UpdateData']['IdentityGuid']
                        genplus_tasks.delete_user.apply_async(
                            args=[identity_guid]
                        )
                    except KeyError:
                        pass

                updates_batch.append(
                    {
                        "UpdateId": update['UpdateId'],
                        "ReceiptId": update['ReceiptId']
                    },
                )
            if len(updates_batch):
                self.delete_batch(updates_batch)

    def delete_batch(self, batch):
        headers = self.get_header()
        post_data = {'Updates': batch}
        url = self.generate_url(self.DELETE_BATCH.format(self.key), None, provisioning=True)
        response = requests.post(url, json=post_data, headers=headers)
        if response.status_code != HTTPStatus.OK.value:
            logger.exception(response.reason)
        logger.info('Successfully deleted batch {}'.format(str(batch)))

    @staticmethod
    def update_user(data):
        try:
            gen_user = GenUser.objects.filter(Q(user__email=data['UnifyEmailAddress']),
                                              Q(identity_guid=data['IdentityGuid']))
        except KeyError:
            gen_user = GenUser.objects.filter(identity_guid=data['IdentityGuid'])

        if gen_user.exist():
            gen_user.user.first_name = data['FirstName']
            gen_user.user.last_name = data['LastName']
            gen_user.user.save()
        return







