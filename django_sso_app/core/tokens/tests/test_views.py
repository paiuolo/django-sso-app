from django.urls import reverse

from rest_framework import status

from django_sso_app.core.tests.factories import UserTestCase


class TestTokens(UserTestCase):

    def test_app_shape_uses_settings_secret(self):
        with self.settings(DJANGO_SSO_APP_SHAPE='app', DJANGO_SSO_APP_SERVICE_URL='http://example.com'):
            user = self._get_new_user()
            device = self._get_user_device(user)

            client = self._get_client()
            client.cookies = self._get_valid_jwt_cookie(user.sso_id, user.sso_rev, device.fingerprint)

            response = client.get(
                reverse('django_sso_app_profile:rest-detail', args=(user.sso_app_profile.sso_id,)),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get('sso_id'), str(user.sso_app_profile.sso_id))

        with self.settings(DJANGO_SSO_APP_SHAPE='app', DJANGO_SSO_APP_SERVICE_URL='http://example.com'):
            user = self._get_new_user()
            device = self._get_user_device(user)
            invalid_jwt = self._get_jwt(device, 'invalid_secret')

            client = self._get_client()
            client.cookies = self._get_jwt_cookie(device, invalid_jwt)

            response = client.get(
                reverse('django_sso_app_profile:rest-detail', args=(user.sso_app_profile.sso_id,)),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, 'invalid_jwt is valid')

    def test_app_apigateway_shape_uses_device_secret(self):
        with self.settings(DJANGO_SSO_APP_SHAPE='app_apigateway', DJANGO_SSO_APP_SERVICE_URL='http://example.com'):
            user = self._get_new_user()
            device = self._get_user_device(user)

            client = self._get_client()
            client.cookies = self._get_jwt_cookie(device)

            response = client.get(
                reverse('django_sso_app_profile:rest-detail', args=(user.sso_app_profile.sso_id,)),
                content_type='application/json',
                HTTP_X_CONSUMER_CUSTOM_ID=user.sso_app_profile.sso_id
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get('sso_id'), str(user.sso_app_profile.sso_id))
