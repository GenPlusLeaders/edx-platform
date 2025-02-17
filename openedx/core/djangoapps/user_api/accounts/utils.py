"""
Utility methods for the account settings.
"""


import re
from urllib.parse import urlparse  # pylint: disable=import-error

import waffle
from completion.waffle import ENABLE_COMPLETION_TRACKING_SWITCH
from completion.models import BlockCompletion
from django.conf import settings
from django.utils.translation import ugettext as _
from social_django.models import UserSocialAuth

from common.config.waffle import TEACHER_PROGRESS_TACKING_DISABLED_SWITCH
from common.djangoapps.third_party_auth.config.waffle import ENABLE_MULTIPLE_SSO_ACCOUNTS_ASSOCIATION_TO_SAML_USER
from common.djangoapps.student.models import AccountRecovery, Registration, get_retired_email_by_email
from openedx.core.djangolib.oauth2_retirement_utils import retire_dot_oauth2_models
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.theming.helpers import get_config_value_from_site_or_settings, get_current_site
from openedx.core.djangoapps.user_api.config.waffle import ENABLE_MULTIPLE_USER_ENTERPRISES_FEATURE
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from ..models import UserRetirementStatus

ENABLE_SECONDARY_EMAIL_FEATURE_SWITCH = 'enable_secondary_email_feature'


def validate_social_link(platform_name, new_social_link):
    """
    Given a new social link for a user, ensure that the link takes one of the
    following forms:

    1) A valid url that comes from the correct social site.
    2) A valid username.
    3) A blank value.
    """
    formatted_social_link = format_social_link(platform_name, new_social_link)

    # Ensure that the new link is valid.
    if formatted_social_link is None:
        required_url_stub = settings.SOCIAL_PLATFORMS[platform_name]['url_stub']
        raise ValueError(_('Make sure that you are providing a valid username or a URL that contains "{url_stub}". '
                           'To remove the link from your edX profile, '
                           'leave this field blank.').format(url_stub=required_url_stub))


def format_social_link(platform_name, new_social_link):
    """
    Given a user's social link, returns a safe absolute url for the social link.

    Returns the following based on the provided new_social_link:
    1) Given an empty string, returns ''
    1) Given a valid username, return 'https://www.[platform_name_base][username]'
    2) Given a valid URL, return 'https://www.[platform_name_base][username]'
    3) Given anything unparseable, returns None
    """
    # Blank social links should return '' or None as was passed in.
    if not new_social_link:
        return new_social_link

    url_stub = settings.SOCIAL_PLATFORMS[platform_name]['url_stub']
    username = _get_username_from_social_link(platform_name, new_social_link)
    if not username:
        return None

    # For security purposes, always build up the url rather than using input from user.
    return f'https://www.{url_stub}{username}'


def _get_username_from_social_link(platform_name, new_social_link):
    """
    Returns the username given a social link.

    Uses the following logic to parse new_social_link into a username:
    1) If an empty string, returns it as the username.
    2) Given a URL, attempts to parse the username from the url and return it.
    3) Given a non-URL, returns the entire string as username if valid.
    4) If no valid username is found, returns None.
    """
    # Blank social links should return '' or None as was passed in.
    if not new_social_link:
        return new_social_link

    # Parse the social link as if it were a URL.
    parse_result = urlparse(new_social_link)
    url_domain_and_path = parse_result[1] + parse_result[2]
    url_stub = re.escape(settings.SOCIAL_PLATFORMS[platform_name]['url_stub'])
    username_match = re.search(r'(www\.)?' + url_stub + r'(?P<username>.*?)[/]?$', url_domain_and_path, re.IGNORECASE)
    if username_match:
        username = username_match.group('username')
    else:
        username = new_social_link

    # Ensure the username is a valid username.
    if not _is_valid_social_username(username):
        return None

    return username


def _is_valid_social_username(value):
    """
    Given a particular string, returns whether the string can be considered a safe username.
    This is a very liberal validation step, simply assuring forward slashes do not exist
    in the username.
    """
    return '/' not in value


def retrieve_last_sitewide_block_completed(user):
    """
    Completion utility
    From a given User object retrieve
    the last course block marked as 'completed' and construct a URL

    :param user: obj(User)
    :return: block_lms_url

    """
    if not ENABLE_COMPLETION_TRACKING_SWITCH.is_enabled() or is_staff_progress_tracking_disabled(user):
        return

    latest_completions_by_course = BlockCompletion.latest_blocks_completed_all_courses(user)

    known_site_configs = [
        other_site_config.get_value('course_org_filter') for other_site_config in SiteConfiguration.objects.all()
        if other_site_config.get_value('course_org_filter')
    ]

    current_site_configuration = get_config_value_from_site_or_settings(
        name='course_org_filter',
        site=get_current_site()
    )

    # courses.edx.org has no 'course_org_filter'
    # however the courses within DO, but those entries are not found in
    # known_site_configs, which are White Label sites
    # This is necessary because the WL sites and courses.edx.org
    # have the same AWS RDS mySQL instance
    candidate_course = None
    candidate_block_key = None
    latest_date = None
    # Go through dict, find latest
    for course, [modified_date, block_key] in latest_completions_by_course.items():
        if not current_site_configuration:
            # This is a edx.org
            if course.org in known_site_configs:
                continue
            if not latest_date or modified_date > latest_date:
                candidate_course = course
                candidate_block_key = block_key
                latest_date = modified_date

        else:
            # This is a White Label site, and we should find candidates from the same site
            if course.org not in current_site_configuration:
                # Not the same White Label, or a edx.org course
                continue
            if not latest_date or modified_date > latest_date:
                candidate_course = course
                candidate_block_key = block_key
                latest_date = modified_date

    if not candidate_course:
        return

    lms_root = SiteConfiguration.get_value_for_org(candidate_course.org, "LMS_ROOT_URL", settings.LMS_ROOT_URL)

    try:
        item = modulestore().get_item(candidate_block_key, depth=1)
    except ItemNotFoundError:
        item = None

    if not (lms_root and item):
        return

    return "{lms_root}/courses/{course_key}/jump_to/{location}".format(
        lms_root=lms_root,
        course_key=str(item.location.course_key),
        location=str(item.location),
    )


def is_secondary_email_feature_enabled():
    """
    Checks to see if the django-waffle switch for enabling the secondary email feature is active

    Returns:
        Boolean value representing switch status
    """
    return waffle.switch_is_active(ENABLE_SECONDARY_EMAIL_FEATURE_SWITCH)


def is_multiple_user_enterprises_feature_enabled():
    """
    Checks to see if the django-waffle switch for enabling the multiple user enterprises feature is active

    Returns:
        Boolean value representing switch status
    """
    return ENABLE_MULTIPLE_USER_ENTERPRISES_FEATURE.is_enabled()


def is_multiple_sso_accounts_association_to_saml_user_enabled():
    """
    Checks to see if the django-waffle switch for enabling the multiple sso accounts association to saml user is active

    Returns:
        Boolean value representing switch status
    """
    return ENABLE_MULTIPLE_SSO_ACCOUNTS_ASSOCIATION_TO_SAML_USER.is_enabled()


def create_retirement_request_and_deactivate_account(user):
    """
    Adds user to retirement queue, unlinks social auth accounts, changes user passwords
    and delete tokens and activation keys
    """
    # Add user to retirement queue.
    UserRetirementStatus.create_retirement(user)

    # Unlink LMS social auth accounts
    UserSocialAuth.objects.filter(user_id=user.id).delete()

    # Change LMS password & email
    user.email = get_retired_email_by_email(user.email)
    user.set_unusable_password()
    user.save()

    # TODO: Unlink social accounts & change password on each IDA.
    # Remove the activation keys sent by email to the user for account activation.
    Registration.objects.filter(user=user).delete()

    # Delete OAuth tokens associated with the user.
    retire_dot_oauth2_models(user)
    AccountRecovery.retire_recovery_email(user.id)


def is_staff_progress_tracking_disabled(user):
    user_is_staff = user.gen_user.is_teacher
    return user_is_staff and TEACHER_PROGRESS_TACKING_DISABLED_SWITCH.is_enabled()
