from django.contrib.auth import get_user_model

from django.urls import reverse

from rest_framework import status
from django_sso_app.core import app_settings
from django_sso_app.core.tests.factories import UserTestCase, responses


from django_sso_app.core.apps.profiles.models import Profile

User = get_user_model()


class TestApp(UserTestCase):

    @responses.activate
    def test_can_replicate_remote_profile(self):

        with self.settings(DJANGO_SSO_APP_SHAPE='app_persistence',
                           DJANGO_SSO_APP_SERVICE_URL='http://example.com'):

            remote_profile_uuid = self._get_random_uuid()

            remote_user_group_name = self._get_random_string()

            remote_user_object = self._get_remote_user_object(uuid=remote_profile_uuid,
                                                              service_name='example.com',
                                                              group_name=remote_user_group_name)

            mocked_url = app_settings.REMOTE_USER_URL.format(sso_id=remote_profile_uuid)
            profile_url = reverse('django_sso_app_profile:rest-detail', args=(remote_profile_uuid,))

            self._set_mocked_response(mocked_url, remote_user_object)

            client = self._get_client()
            client.cookies = self._get_valid_jwt_cookie(remote_profile_uuid, sso_rev=remote_user_object['sso_rev'])

            response = client.get(
                profile_url,
                content_type='application/json'
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get('sso_id'), remote_profile_uuid, 'sso_id differs from remote and local')

            created_profile = Profile.objects.filter(sso_id=remote_profile_uuid).first()

            self.assertEqual(created_profile.groups.count(), 1, 'no profile groups created')
            self.assertEqual(created_profile.groups.filter(name=remote_user_group_name).count(), 1,
                             'users group missing')

            self.assertEqual(created_profile.sso_rev, remote_user_object['sso_rev'], 'sso rev differs')

    @responses.activate
    def test_can_replicate_remote_profile_with_apigateway(self):

        with self.settings(DJANGO_SSO_APP_SHAPE='app_persistence_apigateway',
                           DJANGO_SSO_APP_SERVICE_URL='http://example.com'):

            remote_profile_uuid = self._get_random_uuid()

            remote_user_group_name = self._get_random_string()

            remote_user_object = self._get_remote_user_object(uuid=remote_profile_uuid,
                                                              service_name='example.com',
                                                              group_name=remote_user_group_name)

            mocked_url = app_settings.REMOTE_USER_URL.format(sso_id=remote_profile_uuid)
            profile_url = reverse('django_sso_app_profile:rest-detail', args=(remote_profile_uuid,))

            self._set_mocked_response(mocked_url, remote_user_object)

            client = self._get_client()
            client.cookies = self._get_valid_jwt_cookie(remote_profile_uuid)

            response = client.get(
                profile_url,
                content_type='application/json',
                HTTP_X_CONSUMER_CUSTOM_ID=remote_profile_uuid,
                HTTP_X_CONSUMER_GROUPS=remote_user_group_name
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get('sso_id'), remote_profile_uuid, 'sso_id differs from remote and local')

            created_profile = Profile.objects.filter(sso_id=remote_profile_uuid).first()
            # self.assertEqual(response.data.get('sso_id'), remote_profile_uuid, 'sso_id differs from remote and local')

            self.assertEqual(created_profile.groups.count(), 1, 'no profile groups created')
            self.assertEqual(created_profile.groups.filter(name=remote_user_group_name).count(), 1,
                             'users group missing')

    def test_can_login_by_apigateway_header(self):

        with self.settings(DJANGO_SSO_APP_SHAPE='app_apigateway'):

            remote_profile_uuid = self._get_random_uuid()
            remote_user_group_name = self._get_random_string()

            profile_url = reverse('django_sso_app_profile:rest-detail', args=(remote_profile_uuid,))

            client = self._get_client()
            client.cookies = self._get_valid_jwt_cookie(remote_profile_uuid)

            response = client.get(
                profile_url,
                content_type='application/json',
                HTTP_X_CONSUMER_CUSTOM_ID=remote_profile_uuid,
                HTTP_X_CONSUMER_GROUPS=remote_user_group_name
            )

            created_profile = Profile.objects.get(sso_id=remote_profile_uuid)
            self.assertEqual(created_profile.is_incomplete, True)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get('sso_id'), remote_profile_uuid, 'sso_id differs from header')

            created_profile = Profile.objects.get(sso_id=remote_profile_uuid)

            self.assertEqual(Profile.objects.filter(sso_id=remote_profile_uuid).count(), 1, 'no new user created')
            self.assertEqual(created_profile.groups.count(), 1, 'group not created')
            self.assertEqual(created_profile.groups.filter(name=remote_user_group_name).count(), 1,
                             'group not equals header defined')

    @responses.activate
    def test_redirect_to_service_tos_if_service_not_subscribed(self):
        BACKEND_URL = 'http://accounts.example.com'
        SERVICE_URL = 'http://example.com'

        with self.settings(DJANGO_SSO_APP_SHAPE='app_persistence',
                           DJANGO_SSO_APP_BACKEND_URL=BACKEND_URL,
                           DJANGO_SSO_APP_SERVICE_URL=SERVICE_URL):
            # deleting pre generated user
            remote_profile_uuid = self._get_random_uuid()

            remote_user_group_name = self._get_random_string()

            remote_user_object = self._get_remote_user_object(uuid=remote_profile_uuid,
                                                              service_name='example.com',
                                                              group_name=remote_user_group_name,
                                                              service_subscribed=False)

            mocked_url = app_settings.REMOTE_USER_URL.format(sso_id=remote_profile_uuid)
            #profile_url = reverse('django_sso_app_profile:rest-detail', args=(remote_profile_uuid,))

            self._set_mocked_response(mocked_url, remote_user_object)

            client = self._get_client()
            client.cookies = self._get_valid_jwt_cookie(remote_profile_uuid)

            response = client.get(
                '/',
                content_type='application/json'
            )

            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
            self.assertEqual(response.url, BACKEND_URL + reverse('account_login') + '?next=http%3A%2F%2Fexample.com')

            created_profile = Profile.objects.filter(sso_id=remote_profile_uuid).first()

            self.assertEqual(created_profile.groups.count(), 1, 'no profile groups created')
            self.assertEqual(created_profile.groups.filter(name=remote_user_group_name).count(), 1,
                             'users group missing')

    @responses.activate
    def test_redirect_to_service_tos_if_service_not_subscribed_apigateway(self):
        BACKEND_URL = 'http://accounts.example.com'
        SERVICE_URL = 'http://example.com'

        with self.settings(DJANGO_SSO_APP_SHAPE='app_persistence',
                           DJANGO_SSO_APP_BACKEND_URL=BACKEND_URL,
                           DJANGO_SSO_APP_SERVICE_URL=SERVICE_URL):
            # deleting pre generated user
            remote_profile_uuid = self._get_random_uuid()

            remote_user_group_name = self._get_random_string()

            remote_user_object = self._get_remote_user_object(uuid=remote_profile_uuid,
                                                              service_name='example.com',
                                                              group_name=remote_user_group_name,
                                                              service_subscribed=False)

            mocked_url = app_settings.REMOTE_USER_URL.format(sso_id=remote_profile_uuid)
            #profile_url = reverse('django_sso_app_profile:rest-detail', args=(remote_profile_uuid,))

            self._set_mocked_response(mocked_url, remote_user_object)

            client = self._get_client()
            client.cookies = self._get_valid_jwt_cookie(remote_profile_uuid)

            response = client.get(
                '/',
                content_type='application/json'
            )

            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
            self.assertEqual(response.url, BACKEND_URL + reverse('account_login') + '?next=http%3A%2F%2Fexample.com')

            created_profile = Profile.objects.filter(sso_id=remote_profile_uuid).first()

            self.assertEqual(created_profile.groups.count(), 1, 'no profile groups created')
            self.assertEqual(created_profile.groups.filter(name=remote_user_group_name).count(), 1,
                             'users group missing')

    @responses.activate
    def test_redirect_to_profile_complete_if_profile_is_incomplete(self):
        BACKEND_URL = 'http://accounts.example.com'
        SERVICE_URL = 'http://example.com'

        with self.settings(DJANGO_SSO_APP_SHAPE='app_persistence',
                           DJANGO_SSO_APP_BACKEND_URL=BACKEND_URL,
                           DJANGO_SSO_APP_SERVICE_URL=SERVICE_URL):

            remote_profile_uuid = self._get_random_uuid()

            remote_user_group_name = self._get_random_string()

            remote_user_object = self._get_remote_user_object(uuid=remote_profile_uuid,
                                                              service_name='example.com',
                                                              group_name=remote_user_group_name,
                                                              service_subscribed=True,
                                                              incomplete=True)

            mocked_url = app_settings.REMOTE_USER_URL.format(sso_id=remote_profile_uuid)
            #profile_url = reverse('django_sso_app_profile:rest-detail', args=(remote_profile_uuid,))

            self._set_mocked_response(mocked_url, remote_user_object)

            client = self._get_client()
            client.cookies = self._get_valid_jwt_cookie(remote_profile_uuid)

            response = client.get(
                '/',
                content_type='application/json'
            )

            self.assertEqual(Profile.objects.get(sso_id=remote_profile_uuid).is_incomplete, True)

            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
            self.assertEqual(response.url, BACKEND_URL + '/profile/complete/' + '?next=http%3A%2F%2Fexample.com')

            created_profile = Profile.objects.filter(sso_id=remote_profile_uuid).first()

            self.assertNotEqual(created_profile, None, 'incomplete user not created')

    @responses.activate
    def test_redirect_to_profile_complete_if_profile_is_incomplete_apigateway(self):
        BACKEND_URL = 'http://accounts.example.com'
        SERVICE_URL = 'http://example.com'

        with self.settings(DJANGO_SSO_APP_SHAPE='app_persistence_apigateway',
                           DJANGO_SSO_APP_BACKEND_URL=BACKEND_URL,
                           DJANGO_SSO_APP_SERVICE_URL=SERVICE_URL):
            # deleting pre generated user
            remote_profile_uuid = self._get_random_uuid()

            remote_user_group_name = self._get_random_string()

            remote_user_object = self._get_remote_user_object(uuid=remote_profile_uuid,
                                                              service_name='example.com',
                                                              group_name=remote_user_group_name,
                                                              service_subscribed=True,
                                                              incomplete=True)

            mocked_url = app_settings.REMOTE_USER_URL.format(sso_id=remote_profile_uuid)
            # profile_url = reverse('django_sso_app_profile:rest-detail', args=(remote_profile_uuid,))

            self._set_mocked_response(mocked_url, remote_user_object)

            client = self._get_client()
            client.cookies = self._get_valid_jwt_cookie(remote_profile_uuid)

            response = client.get(
                '/',
                content_type='application/json',
                HTTP_X_CONSUMER_CUSTOM_ID=remote_profile_uuid,
                HTTP_X_CONSUMER_GROUPS=remote_user_group_name
            )

            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
            self.assertEqual(response.url, BACKEND_URL + '/profile/complete/' + '?next=http%3A%2F%2Fexample.com')

            created_profile = Profile.objects.filter(sso_id=remote_profile_uuid).first()

            self.assertNotEqual(created_profile, None, 'incomplete user not created')
