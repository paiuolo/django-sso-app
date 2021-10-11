from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail

from rest_framework import status

from allauth.account.models import EmailConfirmationHMAC, EmailAddress

from django_sso_app.core.tests.factories import UserTestCase

from django_sso_app.core.apps.profiles.models import Profile

User = get_user_model()


class TestBackend(UserTestCase):

    def test_can_login_by_apigateway_header(self):
        with self.settings(DJANGO_SSO_APP_SHAPE='backend_only_apigateway'):
            new_pass = self._get_random_pass()
            new_user = self._get_new_user(password=new_pass)

            profile_url = reverse('django_sso_app_profile:rest-detail', args=(new_user.sso_id,))

            user_device = self._get_user_device(new_user)

            client = self._get_client()
            client.cookies = self._get_jwt_cookie(user_device)

            response = client.get(
                profile_url,
                content_type='application/json',
                HTTP_X_CONSUMER_CUSTOM_ID=new_user.sso_app_profile.sso_id
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get('sso_id'), new_user.sso_id, 'sso_id differs from header')
            self.assertEqual(Profile.objects.filter(sso_id=new_user.sso_id).count(), 1, 'no new user created')

    def test_redirect_to_profile_complete_if_profile_is_incomplete(self):
        BACKEND_URL = 'http://accounts.example.com'

        with self.settings(DJANGO_SSO_APP_SHAPE='backend_only',  APP_URL=BACKEND_URL):

            new_pass = self._get_random_pass()
            new_user = self._get_new_incomplete_user(password=new_pass)

            user_device = self._get_user_device(new_user)

            client = self._get_client()
            client.cookies = self._get_jwt_cookie(user_device)

            response = client.get(
                '/profile/',
                content_type='application/json',
                HTTP_X_CONSUMER_CUSTOM_ID=new_user.sso_app_profile.sso_id
            )

            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
            self.assertEqual(response.url, '/profile/complete/')

    def test_redirect_to_profile_complete_if_profile_is_incomplete_apigateway(self):

        with self.settings(DJANGO_SSO_APP_SHAPE='backend_app_apigateway'):

            new_pass = self._get_random_pass()
            new_user = self._get_new_incomplete_user(password=new_pass)

            user_device = self._get_user_device(new_user)

            client = self._get_client()
            client.cookies = self._get_jwt_cookie(user_device)

            response = client.get(
                '/profile/',
                content_type='application/json',
                HTTP_X_CONSUMER_CUSTOM_ID=new_user.sso_app_profile.sso_id
            )

            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
            self.assertEqual(response.url, '/profile/complete/')

    def test_email_verification_redirects_to_profile_completion(self):

        with self.settings(DJANGO_SSO_APP_SHAPE='backend_app'):
            signup_obj = self._get_signup_object()

            client = self._get_client()
            response = client.post(
                reverse('account_signup'),
                data=signup_obj
            )

            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
            self.assertEqual(len(mail.outbox), 1)

            email_address = EmailAddress.objects.get(email=signup_obj['email'])
            email_confirmation = EmailConfirmationHMAC(email_address)

            response2 = client.get(reverse('account_confirm_email',
                                   args=[email_confirmation.key]),
                                   follow=True)

            self.assertEqual(response2.redirect_chain[-1][0], '/profile/complete/')

    def test_email_verification_redirects_to_profile_completion_apigateway(self):

        with self.settings(DJANGO_SSO_APP_SHAPE='backend_app'):
            signup_obj = self._get_signup_object()

            client = self._get_client()
            response = client.post(
                reverse('account_signup'),
                data=signup_obj,
            )

            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
            self.assertEqual(len(mail.outbox), 1)

            email_address = EmailAddress.objects.get(email=signup_obj['email'])
            email_confirmation = EmailConfirmationHMAC(email_address)

            new_user = User.objects.get(email=signup_obj['email'])

            response2 = client.get(reverse('account_confirm_email', args=[email_confirmation.key]),
                                   HTTP_X_CONSUMER_CUSTOM_ID=new_user.sso_app_profile.sso_id,
                                   follow=True)

            self.assertEqual(response2.redirect_chain[-1][0], '/profile/complete/')
