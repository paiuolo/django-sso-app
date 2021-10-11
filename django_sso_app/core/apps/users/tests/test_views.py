import json
import jwt

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.core import mail

from allauth.account.adapter import get_adapter
from rest_framework import status

from django_sso_app.core.tests.factories import UserTestCase

from .... import app_settings

User = get_user_model()


class TestUserCreate(UserTestCase):

    def test_staff_user_can_create_user_with_profile_with_unverified_email(self):
        new_staff_user = self._get_new_staff_user()
        new_user_object = self._get_new_user_object()

        new_staff_user_token_headers = self._get_new_api_token_headers(new_staff_user)

        client = self._get_client()
        response = client.post(
            reverse('django_sso_app_user:rest-list'),
            data=json.dumps(new_user_object),
            **new_staff_user_token_headers
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_user_sso_id = response.data.get('sso_id')

        response2 = client.get(
            reverse('django_sso_app_user:rest-detail', args=(new_user_sso_id,)),
            **new_staff_user_token_headers
        )

        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        self.assertEqual(response2.data['email'], new_user_object['email'])
        self.assertEqual(response2.data['email_verified'], False)

    def test_staff_user_can_create_user_with_profile_and_validated_email(self):
        new_staff_user = self._get_new_staff_user()
        new_user_object = self._get_new_user_object()

        new_staff_user_token_headers = self._get_new_api_token_headers(new_staff_user)

        client = self._get_client()
        response = client.post(
            reverse('django_sso_app_user:rest-list') + '?skip_confirmation=true',
            data=json.dumps(new_user_object),
            **new_staff_user_token_headers
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_user_sso_id = response.data.get('sso_id')

        response2 = client.get(
            reverse('django_sso_app_user:rest-detail', args=(new_user_sso_id,)),
            **new_staff_user_token_headers
        )

        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        self.assertEqual(response2.data['email'], new_user_object['email'])
        self.assertEqual(response2.data['email_verified'], True)

    def test_non_staff_user_can_not_create_profile(self):
        new_pass = self._get_random_pass()
        new_user = self._get_new_user(password=new_pass)

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(new_user.email, new_pass)),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_user_object = self._get_new_user_object()

        response = client.post(
            reverse('django_sso_app_user:rest-list') + '?skip_confirmation=true',
            data=json.dumps(new_user_object),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, 'non staff users can create new user')


class TestUserRetrieve(UserTestCase):

    def test_user_can_retrieve_user(self):
        new_pass = self._get_random_pass()
        new_user = self._get_new_user(password=new_pass)

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(new_user.email, new_pass)),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response2 = client.get(
            reverse('django_sso_app_user:rest-detail', args=(new_user.sso_app_profile.sso_id,)),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, status.HTTP_200_OK)

    def test_staff_user_can_retrieve_user_with_token(self):
        new_user = self._get_new_user()
        new_staff_user = self._get_new_staff_user()

        new_staff_user_token_headers = self._get_new_api_token_headers(new_staff_user)

        client = self._get_client()
        response = client.get(
            reverse('django_sso_app_user:rest-detail', args=(new_user.sso_app_profile.sso_id,)),
            **new_staff_user_token_headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestUserUpdate(UserTestCase):

    def test_user_email_update_deletes_all_devices_and_waits_for_confirmation(self):
        new_pass = self._get_random_pass()
        new_user = self._get_new_user(password=new_pass)
        new_user_profile = new_user.sso_app_profile

        first_rev = new_user_profile.sso_rev

        first_email_login = self._get_login_object(new_user.email, new_pass)

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(first_email_login),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_email = self._get_random_email()

        response2 = client.patch(
            reverse('django_sso_app_user:rest-detail', args=[new_user_profile.sso_id]),
            data=json.dumps({
                'email': new_email
            }),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        new_user_profile.refresh_from_db()
        second_rev = new_user_profile.sso_rev

        self.assertEqual(second_rev, first_rev + 1, 'rev not incremented')

        emails = new_user.emailaddress_set.all()
        self.assertEqual(emails.count(), 2, 'email not created')

        self.assertEqual(len(mail.outbox), 1, 'no email sent')

        cofirmation_message = mail.outbox[0]
        recipients = cofirmation_message.recipients()

        self.assertIn(new_email, recipients, 'user email not in recipients')

        client = self._get_client()
        response3 = client.post(
            reverse('rest_login'),
            data=json.dumps(first_email_login),
            content_type='application/json'
        )

        self.assertEqual(response3.status_code, 200, 'unable to login with old email')

        client = self._get_client()
        response4 = client.post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(new_email, new_pass)),
            content_type='application/json'
        )

        self.assertEqual(response4.status_code, 400, 'login with unconfirmed email is still possible')

        unconfirmed_email = new_user.emailaddress_set.get(email=new_email)
        self.assertEqual(unconfirmed_email.verified, False)

        adapter = get_adapter()
        adapter.confirm_email(None, unconfirmed_email)

        client = self._get_client()
        response5 = client.post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(new_email, new_pass)),
            content_type='application/json'
        )

        self.assertEqual(response5.status_code, 200, 'login with confirmed email is not possible')

        self.assertEqual(new_user.emailaddress_set.count(), 1, 'more than 1 email after new email confirmation')

        client = self._get_client()
        response6 = client.post(
            reverse('rest_login'),
            data=json.dumps(first_email_login),
            content_type='application/json'
        )

        self.assertEqual(response6.status_code, 400, 'login old email is still possible')

    def test_user_password_update_refreshes_and_returns_current_device_jwt_and_deletes_all_profile_devices(self):
        new_pass = self._get_random_pass()
        new_user = self._get_new_user(password=new_pass)
        new_user_profile = new_user.sso_app_profile

        first_rev = new_user_profile.sso_rev

        first_email_login = self._get_login_object(new_user.email, new_pass)

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(first_email_login),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        jwt_cookie = self._get_response_jwt_cookie(response)

        self.assertIsNotNone(jwt_cookie, 'no jwt cookie set')

        unverified_payload = jwt.decode(jwt_cookie, None, False)

        updated_pass = self._get_random_pass()

        response2 = client.patch(
            reverse('django_sso_app_user:rest-detail', args=[new_user_profile.sso_id]),
            data=json.dumps({
                'password': updated_pass
            }),
            content_type='application/json'
        )

        new_user_profile.refresh_from_db()
        second_rev = new_user_profile.sso_rev

        self.assertEqual(second_rev, first_rev + 1, 'rev not incremented')

        jwt_cookie2 = self._get_response_jwt_cookie(response2)

        self.assertIsNotNone(jwt_cookie2, 'no jwt cookie set')
        self.assertEqual(new_user_profile.devices.count(), 0, 'other devices not deleted')

        client2 = self._get_client()
        response3 = client2.post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(new_user.email, updated_pass)),
            content_type='application/json'
        )

        self.assertEqual(response3.status_code, 200, 'unable to login with new password')

        jwt_cookie3 = self._get_response_jwt_cookie(response3)
        unverified_payload3 = jwt.decode(jwt_cookie3, None, False)

        self.assertGreater(unverified_payload3.get('sso_rev'), unverified_payload.get('sso_rev'),
                           'rev not incremented after pass update')

    def test_user_password_update_refreshes_profile_even_if_called_with_authorization_headers(self):
        new_pass = self._get_random_pass()
        new_user = self._get_new_user(password=new_pass)
        new_user_profile = new_user.sso_app_profile

        first_rev = new_user_profile.sso_rev

        first_email_login = self._get_login_object(new_user.email, new_pass)

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(first_email_login),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        received_jwt = self._get_response_jwt_cookie(response)
        unverified_payload = jwt.decode(received_jwt, None, False)

        self.assertEqual(response.data['token'], received_jwt, 'jwt differs between cookie and response')

        updated_pass = self._get_random_pass()
        valid_password_update = {
            'password': updated_pass
        }

        response2 = self._get_client().patch(
            reverse('django_sso_app_user:rest-detail', args=[new_user_profile.sso_id]),
            data=json.dumps(valid_password_update),
            content_type='application/json',
            HTTP_AUTHORIZATION='Bearer {}'.format(received_jwt)
        )

        self.assertEqual(response2.status_code, 200, 'cannot patch with jwt header')

        received_jwt2 = self._get_response_jwt_cookie(response2)

        self.assertIsNotNone(received_jwt2, 'no jwt cookie received')

        new_user_profile.refresh_from_db()
        second_rev = new_user_profile.sso_rev

        self.assertEqual(second_rev, first_rev + 1, 'rev not incremented')

        devices = new_user_profile.devices.all()

        self.assertEqual(devices.count(), 0, 'devices not deleted')

        response3 = self._get_client().post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(new_user.email, updated_pass)),
            content_type='application/json'
        )

        self.assertEqual(response3.status_code, 200, 'unable to login with new password')

        jwt_cookie3 = self._get_response_jwt_cookie(response3)
        unverified_payload3 = jwt.decode(jwt_cookie3, None, False)

        self.assertGreater(unverified_payload3.get('sso_rev'), unverified_payload.get('sso_rev'),
                           'rev not increased after pass update')

    def test_user_email_update_by_staff_disables_user_login_user_must_confirm_email(self):
        """
        User update by staff refreshes disables login and deletes all user devices
        """
        new_email = self._get_random_email()
        new_pass = self._get_random_pass()
        new_user = self._get_new_user(email=new_email, password=new_pass)
        new_user_profile = new_user.sso_app_profile

        new_staff_user = self._get_new_staff_user()

        first_rev = new_user_profile.sso_rev

        updated_email = self._get_random_email()

        response = self._get_client().patch(
            reverse('django_sso_app_user:rest-detail', args=[new_user_profile.sso_id]),
            data=json.dumps({
                'email': updated_email
            }),
            **self._get_new_api_token_headers(new_staff_user)
        )

        received_jwt = self._get_response_jwt_cookie(response)

        self.assertIsNone(received_jwt, 'jwt cookie received')

        new_user_profile.refresh_from_db()
        second_rev = new_user_profile.sso_rev

        self.assertEqual(second_rev, first_rev + 1, 'rev not incremented')

        self.assertEqual(new_user_profile.devices.count(), 0, 'user devices not deleted')

        response3 = self._get_client().post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(updated_email, new_pass)),
            content_type='application/json'
        )

        self.assertEqual(response3.status_code, status.HTTP_400_BAD_REQUEST,
                         'user can login without confirming email after update')

        msg = _('We have sent an e-mail to you for verification. '
                'Follow the link provided to finalize the signup process. '
                'Please contact us if you do not receive it within a few minutes.')
        self.assertEqual(response3.data, msg)

        response4 = self._get_client().post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(new_email, new_pass)),
            content_type='application/json'
        )

        self.assertEqual(response4.status_code, status.HTTP_200_OK, 'user can not login with old confirmed email')

    def test_user_email_update_by_staff_with_skip_email_confirmation_activates_new_email(self):
        """
        User update by staff refreshes disables login and deletes all user devices
        """
        new_email = self._get_random_email()
        new_pass = self._get_random_pass()
        new_user = self._get_new_user(email=new_email, password=new_pass)
        new_user_profile = new_user.sso_app_profile

        new_staff_user = self._get_new_staff_user()

        first_rev = new_user_profile.sso_rev

        updated_email = self._get_random_email()

        response = self._get_client().patch(
            reverse('django_sso_app_user:rest-detail', args=[new_user_profile.sso_id]) + '?skip_confirmation=true',
            data=json.dumps({
                'email': updated_email
            }),
            **self._get_new_api_token_headers(new_staff_user)
        )

        received_jwt = self._get_response_jwt_cookie(response)

        self.assertIsNone(received_jwt, 'jwt cookie received')

        new_user_profile.refresh_from_db()
        second_rev = new_user_profile.sso_rev

        self.assertEqual(second_rev, first_rev + 1, 'rev not incremented')

        self.assertEqual(new_user_profile.devices.count(), 0, 'user devices not deleted')

        response2 = self._get_client().post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(updated_email, new_pass)),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, status.HTTP_200_OK, 'user can not login with old confirmed email')
