import logging

from allauth.account.models import (
    EmailAddress,
)
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.test.utils import override_settings

from rest_framework import status

from allauth.account.adapter import get_adapter

from .factories import UserTestCase

User = get_user_model()
logger = logging.getLogger('django_sso_app')


class TestLogin(UserTestCase):
    def test_can_login_with_email(self):
        new_pass = self._get_random_pass()
        new_user = self._get_new_user(password=new_pass)

        client = self._get_client()

        response = client.post(
            reverse('account_login'),
            data=self._get_login_object(new_user.email, new_pass)
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '/')
        self.assertIsNotNone(self._get_response_jwt_cookie(response), 'response has no jwt cookie')

    def test_can_login_with_username(self):
        new_pass = self._get_random_pass()
        new_user = self._get_new_user(password=new_pass)

        client = self._get_client()
        response = client.post(
            reverse('account_login'),
            data=self._get_login_object(new_user.username, new_pass)
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '/')
        self.assertIsNotNone(self._get_response_jwt_cookie(response), 'response has no jwt cookie')

    def test_admin_user_do_not_receives_jwt_on_login(self):
        new_admin_pass = self._get_random_pass()
        new_admin_user = self._get_new_admin_user(password=new_admin_pass)

        response = self.client.post(
            '/admin/login/',
            data=self._get_login_object(new_admin_user.username, new_admin_pass)
        )

        self.assertIsNone(self._get_response_jwt_cookie(response), 'admin receives jwt')

    def test_django_superuser_can_not_login_from_default_views(self):
        new_admin_pass = self._get_random_pass()
        new_admin_user = self._get_new_admin_user(password=new_admin_pass)

        client = self._get_client()
        response = client.post(
            reverse('account_login'),
            data=self._get_login_object(new_admin_user.username, new_admin_pass)
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIsNone(self._get_response_jwt_cookie(response), 'admin receives jwt')

    def test_django_staff_user_can_not_login_from_default_views(self):
        new_staff_pass = self._get_random_pass()
        new_staff_user = self._get_new_staff_user(password=new_staff_pass)

        client = self._get_client()
        response = client.post(
            reverse('account_login'),
            data=self._get_login_object(new_staff_user.username, new_staff_pass)
        )
        print('RESP', response)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIsNone(self._get_response_jwt_cookie(response), 'staff receives jwt')

    def test_user_must_complete_profile(self):
        new_pass = self._get_random_pass()
        new_user = self._get_new_incomplete_user(password=new_pass)

        client = self._get_client()
        response = client.post(
            reverse('account_login'),
            data=self._get_login_object(new_user.email, new_pass),
            follow=True
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._test_response_path(response, reverse('profile.complete'))
        self.assertIsNotNone(self._get_response_jwt_cookie(response), 'incomplete user do not receives jwt')


class TestLogout(UserTestCase):

    @override_settings(DJANGO_SSO_APP_LOGOUT_DELETES_ALL_PROFILE_DEVICES=True)
    def test_logout_deletes_jwt_and_removes_all_profile_devices(self):
        new_pass = self._get_random_pass()
        new_user = self._get_new_user(password=new_pass)

        client = self._get_client()
        response = client.post(
            reverse('account_login'),
            data=self._get_login_object(new_user.email, new_pass)
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        response2 = client.post(
            reverse('account_logout')
        )

        self.assertEqual(self._get_response_jwt_cookie(response2), '', 'api logout keeps jwt cookie')

        user_devices_post_logout = new_user.sso_app_profile.devices.all()

        self.assertEqual(user_devices_post_logout.count(), 0,
                         'api logout is not deleting all profile devices')

    @override_settings(DJANGO_SSO_APP_LOGOUT_DELETES_ALL_PROFILE_DEVICES=False)
    def test_logout_deletes_jwt_and_removes_caller_device(self):
        new_pass = self._get_random_pass()
        new_user = self._get_new_user(password=new_pass)

        client = self._get_client()
        response = client.post(
            reverse('account_login'),
            data=self._get_login_object(new_user.email, new_pass)
        )

        print('RE0,', response, response.status_code)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        user_devices_pre_logout = new_user.sso_app_profile.devices.all()

        response2 = client.post(
            reverse('account_logout')
        )

        self.assertEqual(self._get_response_jwt_cookie(response2), '', 'api logout keeps jwt cookie')

        user_devices_post_logout = new_user.sso_app_profile.devices.all()

        self.assertEqual(user_devices_post_logout.count(), user_devices_pre_logout.count(),
                         'api logout is deleting all profile devices')


class TestSignup(UserTestCase):
    def test_can_register(self):
        signup_obj = self._get_signup_object()

        client = self._get_client()
        response = client.post(
            reverse('account_signup'),
            data=signup_obj
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        new_user = User.objects.filter(email=signup_obj['email']).first()

        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.email, signup_obj['email'])

        email_address = EmailAddress.objects.filter(user=new_user, email=signup_obj['email']).first()

        self.assertNotEqual(email_address, None)

    def test_cannot_register_on_invalid_registration_data(self):
        users_count_before = User.objects.count()

        signup_obj = self._get_invalid_signup_object()

        client = self._get_client()
        response = client.post(
            reverse('account_signup'),
            data=signup_obj
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        users_count_after = User.objects.count()

        self.assertEqual(users_count_before, users_count_after)

    def test_registration_sends_confirmation_email(self):
        signup_obj = self._get_signup_object()

        client = self._get_client()
        response = client.post(
            reverse('account_signup'),
            data=signup_obj
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(len(mail.outbox), 1)

    def test_registration_do_not_update_sso_rev(self):
        signup_obj = self._get_signup_object()

        client = self._get_client()
        response = client.post(
            reverse('account_signup'),
            data=signup_obj
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        new_user = User.objects.get(email=signup_obj['email'])

        self.assertEqual(new_user.sso_app_profile.sso_rev, 1)

    def test_registration_creates_subscription(self):
        new_service = self._get_new_service()
        signup_obj = self._get_subscribe_signup_object(new_service.service_url)

        client = self._get_client()
        response = client.post(
            reverse('account_signup'),
            data=signup_obj
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        new_user = User.objects.filter(email=signup_obj['email']).first()
        self.assertNotEqual(new_user, None, 'no new user')

        self.assertEqual(new_user.sso_app_profile.subscriptions.filter(service__service_url=
                                                                       new_service.service_url).count(), 1)

    def test_created_user_incomplete_profile_has_username_set_to_email(self):
        signup_obj = self._get_signup_object()

        client = self._get_client()
        response = client.post(
            reverse('account_signup'),
            data=signup_obj
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        new_user = User.objects.filter(username=signup_obj['email']).first()
        self.assertNotEqual(new_user, None, 'no new user with username as email')

    def test_created_user_with_incomplete_profile_enters_incomplete_group(self):
        signup_obj = self._get_signup_object()

        client = self._get_client()
        response = client.post(
            reverse('account_signup'),
            data=signup_obj
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        new_user = User.objects.filter(email=signup_obj['email']).first()
        self.assertNotEqual(new_user, None, 'no new incomplete user')

        unconfirmed_email = new_user.emailaddress_set.get(email=signup_obj['email'])
        self.assertEqual(unconfirmed_email.verified, False)

        adapter = get_adapter()
        adapter.confirm_email(None, unconfirmed_email)

        new_pass = signup_obj['password1']
        client = self._get_client()
        response = client.post(
            reverse('account_login'),
            data=self._get_login_object(new_user.email, new_pass),
            follow=True
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._test_response_path(response, reverse('profile.complete'))
        self.assertIsNotNone(self._get_response_jwt_cookie(response), 'incomplete user do not receives jwt')

        self.assertEqual(new_user.sso_app_profile.is_incomplete, True)

        self.assertIsNotNone(new_user.sso_app_profile.groups.filter(name='incomplete').first(),
                             'incomplete user did not enter "incomplete" group on login')
