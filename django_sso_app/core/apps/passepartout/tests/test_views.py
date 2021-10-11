from django.utils.http import urlencode

from django.urls import reverse

from rest_framework import status

from django_sso_app.core.tests.factories import UserTestCase, responses

from ..models import Passepartout


class TestPassepartout(UserTestCase):

    def test_can_login_on_multiple_domains(self):

        with self.settings(DJANGO_SSO_APP_SHAPE='backend_only',
                           APP_DOMAIN='example.com',
                           DJANGO_SSO_APP_BACKEND_DOMAINS=['example.com', 'example.org']):

            new_pass = self._get_random_pass()
            new_user = self._get_new_user(password=new_pass)
            profile = new_user.sso_app_profile

            client = self._get_client()
            response = client.post(
                reverse('account_login'),
                data=self._get_login_object(new_user.email, new_pass)
            )

            self.assertEqual(response.status_code, status.HTTP_302_FOUND)

            self.assertEqual(Passepartout.objects.count(), 1)

            passepartout_object = Passepartout.objects.first()

            passepartout_url = 'http://' + 'example.org' + reverse('django_sso_app_passepartout:login',
                                                                   args=[passepartout_object.token]) + '?' + urlencode({'next':'http://example.com'})
            passepartout_response_url = response.url

            self.assertEqual(passepartout_response_url, passepartout_url)

            self.assertIsNotNone(self._get_response_jwt_cookie(response), 'response has no jwt cookie')

            with self.settings(APP_DOMAIN='example.org', COOKIE_DOMAIN='example.org'):
                response3 = client.get(
                    passepartout_response_url
                )

                self.assertEqual(response3.status_code, status.HTTP_302_FOUND)
                self.assertIsNotNone(self._get_response_jwt_cookie(response3), 'response 2 has no jwt cookie')
                self.assertEqual(response3.url, 'http://' + 'example.com')

                response4 = client.get(
                    reverse('django_sso_app_profile:rest-detail', args=(profile.sso_id,)),
                    content_type='application/json'
                )

                self.assertEqual(response4.status_code, status.HTTP_200_OK)

                passepartout_object.refresh_from_db()
                self.assertEqual(passepartout_object.is_active, False)

                response5 = client.get(
                    passepartout_response_url
                )

                self.assertEqual(response5.status_code, status.HTTP_302_FOUND)
                self.assertEqual(response5.url, reverse('account_login'))


            response6 = client.get(
                reverse('django_sso_app_profile:rest-detail', args=(profile.sso_id,)),
                content_type='application/json'
            )

            self.assertEqual(response6.status_code, status.HTTP_200_OK)
