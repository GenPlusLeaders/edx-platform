"""
Tests for RequiredFieldsData View
"""
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory


@skip_unless_lms
class RequiredFieldsDataViewTest(APITestCase):
    """
    Tests for the end-point that returns required fields.
    """

    def setUp(self):
        super().setUp()

        self.user = UserFactory.create(username='test_user', password='password123')
        self.client.force_authenticate(user=self.user)
        self.url = reverse('required_fields')

    def test_unauthenticated_request_is_forbidden(self):
        """
        Test that unauthenticated user should not be able to access the endpoint.
        """
        self.client.logout()
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @override_settings(REGISTRATION_EXTRA_FIELDS={"first_name": "optional", "city": "optional"})
    def test_required_fields_not_configured(self):
        """
        Test that when no required fields are configured in REGISTRATION_EXTRA_FIELDS
        settings, then API returns proper response.
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get('error_code') == 'required_fields_configured_incorrectly'
