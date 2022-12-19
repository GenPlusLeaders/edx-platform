import logging
from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute
from openedx.features.genplus_features.genplus.rmunify import RmUnify
from openedx.features.genplus_features.genplus.models import School, Class, GenUser
from django.contrib.auth.models import User

log = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def sync_schools(self, class_type, school_ids):
    schools = School.objects.filter(guid__in=school_ids)
    rm_unify = RmUnify()
    rm_unify.fetch_classes(class_type, queryset=schools)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def sync_student(self, class_ids):
    queryset = Class.objects.filter(id__in=class_ids)
    rm_unify = RmUnify()
    rm_unify.fetch_students(query=queryset)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
@set_code_owner_attribute
def delete_user(self, guid):
    try:
        gen_user = GenUser.objects.get(identity_guid=guid)
        if hasattr(gen_user, 'user'):
            User.objects.filter(pk=gen_user.user.pk).delete()
        else:
            # case where user is not logged into our system
            gen_user.delete()
        log.info(
            'User with identity_guid {} has been deleted.'.format(guid)
        )
    except GenUser.DoesNotExist:
        log.exception(
            'User with identity_guid {} does not exist.'.format(guid)
        )

