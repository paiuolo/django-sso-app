import json

from django.contrib.auth import get_user_model

from django.urls import reverse

from rest_framework import status
from django_sso_app.core.tests.factories import UserTestCase, responses

from django_sso_app.core.apps.profiles.models import Profile


class TestStatus(UserTestCase):

    def setUp(self):
        self.service = self._get_new_service('example.com')
        self.new_pass = self._get_random_pass()
        self.new_user = self._get_new_subscribed_user(password=self.new_pass, service=self.service)
        self.new_user_profile = self.new_user.sso_app_profile
        self.new_user_profile.groups.add(self._get_new_group())

    @responses.activate
    def test_switch_between_statuses(self):
        with self.settings(DJANGO_SSO_APP_SHAPE='backend_only'):

            response = self._get_client().post(
                reverse('rest_login'),
                data=json.dumps(self._get_login_object(self.new_user.email, self.new_pass)),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK, 'new user can not login')

        with self.settings(DJANGO_SSO_APP_SHAPE='backend_app'):
            response2 = self._get_client().post(
                reverse('rest_login'),
                data=json.dumps(self._get_login_object(self.new_user.email, self.new_pass)),
                content_type='application/json'
            )

            self.assertEqual(response2.status_code, status.HTTP_200_OK, 'new user can not login')

        with self.settings(DJANGO_SSO_APP_SHAPE='app',
                           DJANGO_SSO_APP_SERVICE_URL='http://example.com'):

            device = self.new_user_profile.devices.first()

            jwt_cookie = self._get_jwt_cookie(device)

            client = self._get_client()
            client.cookies = jwt_cookie

            response = client.get(
                reverse('django_sso_app_profile:rest-detail', args=(self.new_user_profile.sso_id,)),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK, 'unable to get profile detail')

            self.assertEqual(Profile.objects.filter(sso_id=self.new_user_profile.sso_id).count(), 1,
                             'no profile model created')

            self.assertEqual(response.data.get('sso_id'), str(self.new_user_profile.sso_id), 'sso_id differs')

        with self.settings(DJANGO_SSO_APP_SHAPE='app_persistence',
                           DJANGO_SSO_APP_SERVICE_URL='http://example.com'):

            device = self.new_user_profile.devices.first()
            jwt_cookie = self._get_jwt_cookie(device)

            client = self._get_client()
            client.cookies = jwt_cookie

            response = client.get(
                reverse('django_sso_app_profile:rest-detail', args=(self.new_user_profile.sso_id,)),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK, 'unable to get profile detail')

            self.assertEqual(Profile.objects.filter(sso_id=self.new_user_profile.sso_id).count(), 1,
                             'no profile model created')

            self.assertEqual(response.data.get('sso_id'), str(self.new_user_profile.sso_id), 'sso_id differs')

        with self.settings(DJANGO_SSO_APP_SHAPE='app_apigateway',
                           DJANGO_SSO_APP_SERVICE_URL='http://example.com'):

            device = self.new_user_profile.devices.first()
            jwt_cookie = self._get_jwt_cookie(device)

            remote_profile_uuid = self.new_user_profile.sso_id
            remote_user_group_name = self.new_user_profile.groups.first().name

            profile_url = reverse('django_sso_app_profile:rest-detail', args=(remote_profile_uuid,))

            client = self._get_client()
            client.cookies = jwt_cookie

            response = client.get(
                profile_url,
                content_type='application/json',
                HTTP_X_CONSUMER_CUSTOM_ID=remote_profile_uuid,
                HTTP_X_CONSUMER_GROUPS=remote_user_group_name
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get('sso_id'), remote_profile_uuid, 'sso_id differs from header')

        with self.settings(DJANGO_SSO_APP_SHAPE='app_persistence_apigateway',
                           DJANGO_SSO_APP_SERVICE_URL='http://example.com'):

            device = self.new_user_profile.devices.first()
            jwt_cookie = self._get_jwt_cookie(device)

            remote_profile_uuid = self.new_user_profile.sso_id
            remote_user_group_name = self.new_user_profile.groups.first().name

            profile_url = reverse('django_sso_app_profile:rest-detail', args=(remote_profile_uuid,))

            client = self._get_client()
            client.cookies = jwt_cookie

            response = client.get(
                profile_url,
                content_type='application/json',
                HTTP_X_CONSUMER_CUSTOM_ID=remote_profile_uuid,
                HTTP_X_CONSUMER_GROUPS=remote_user_group_name
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK, 'unable to get profile detail')

            self.assertEqual(Profile.objects.filter(sso_id=self.new_user_profile.sso_id).count(), 1,
                             'no profile model created')

            self.assertEqual(response.data.get('sso_id'), str(self.new_user_profile.sso_id), 'sso_id differs')
