import json

import jwt
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from rest_framework import status

from django_sso_app.core.tests.factories import UserTestCase

User = get_user_model()


class TestProfileRetrieve(UserTestCase):

    def test_user_can_retrieve_profile_with_subscriptions(self):
        """
          Registration via rest_auth view
        """
        new_pass = self._get_random_pass()
        new_user = self._get_new_subscribed_user(password=new_pass)
        profile = new_user.sso_app_profile

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(new_user.email, new_pass)),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response2 = client.get(
            reverse('django_sso_app_profile:rest-detail', args=(profile.sso_id,)),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        self.assertEqual(response2.data.get('subscriptions'),
                         [{'service_url': el.service.service_url, 'is_unsubscribed': el.is_unsubscribed} for el in
                          profile.subscriptions.all()])


class TestProfileUpdate(UserTestCase):

    def test_profile_update_refreshes_and_returns_current_device_jwt_and_deletes_other_devices(self):
        """
        Profile update refreshes caller jwt and deletes all but caller devices
        """
        new_pass = self._get_random_pass()
        new_user = self._get_new_user(password=new_pass)

        profile = new_user.sso_app_profile
        first_rev = profile.sso_rev

        login_object = self._get_login_object(new_user.email, new_pass)

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(login_object),
            content_type='application/json'
        )

        cookies = response.cookies

        profile_update = self._get_new_profile_object()

        response2 = client.patch(
            reverse('django_sso_app_profile:rest-detail', args=[profile.sso_id]),
            data=json.dumps(profile_update),
            content_type='application/json'
        )

        cookies2 = response2.cookies

        profile.refresh_from_db()
        second_rev = profile.sso_rev

        self.assertEqual(second_rev, first_rev + 1, 'rev not incremented')

        self.assertNotEqual(self._get_response_jwt_cookie(response2), '', 'profile update do not return jwt cookie')

        devices = profile.devices.all()

        self.assertEqual(devices.count(), 1, 'other devices not deleted')
        self.assertEqual(devices.first().fingerprint, login_object['fingerprint'], 'device not updated')

        jwt_cookie = cookies.get('jwt').value
        jwt_cookie2 = cookies2.get('jwt').value

        # print('\nRISPOSTA, user rev', self.profile.sso_rev, '\n\nTOKEN', jwt_cookie)

        unverified_payload = jwt.decode(jwt_cookie, None, False)
        unverified_payload2 = jwt.decode(jwt_cookie2, None, False)

        self.assertEqual(unverified_payload2.get('sso_rev'), unverified_payload.get('sso_rev') + 1,
                         'rev not incremented in cookie')

        for f in profile_update:
            model_val = getattr(profile, f, None)
            object_val = profile_update.get(f, None)

            if f == 'birthdate':
                model_val = str(model_val)
            elif f == 'expiration_date':
                model_val = model_val.isoformat()
            elif f == 'country':
                object_val = object_val.upper()
                model_val = str(model_val).upper()
            elif f == 'country_of_birth':
                object_val = object_val.upper()
                model_val = str(model_val).upper()

            self.assertEqual(model_val, object_val)


class TestProfileComplete(UserTestCase):

    def test_user_can_complete_profile_with_username_changed(self):
        """
          Registration via rest_auth view
        """
        new_pass = self._get_random_pass()
        new_incomplete_user = self._get_new_incomplete_user(password=new_pass)

        profile = new_incomplete_user.sso_app_profile
        first_rev = profile.sso_rev

        login_object = self._get_login_object(new_incomplete_user.email, new_pass)

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(login_object),
            content_type='application/json'
        )

        cookies = response.cookies
        print('RESP', response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile_complete = {
            'username': self._get_random_username(),
            'profile': self._get_new_profile_object()
        }

        response2 = client.patch(
            reverse('django_sso_app_user:rest-detail', args=[new_incomplete_user.sso_app_profile.sso_id]),
            data=json.dumps(profile_complete),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        new_incomplete_user.refresh_from_db()
        self.assertEqual(new_incomplete_user.username, profile_complete['username'])

        self.assertEqual(new_incomplete_user.sso_app_profile.first_name, profile_complete['profile']['first_name'])

        self.assertEqual(new_incomplete_user.sso_app_profile.is_incomplete, False)

    def test_user_cant_update_username_on_profile_complete(self):
        """
          Registration via rest_auth view
        """
        from django_sso_app import app_settings

        new_pass = self._get_random_pass()
        new_incomplete_user = self._get_new_incomplete_user(password=new_pass)

        profile = new_incomplete_user.sso_app_profile
        first_rev = profile.sso_rev

        login_object = self._get_login_object(new_incomplete_user.email, new_pass)

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(login_object),
            content_type='application/json'
        )

        cookies = response.cookies
        print('RESP', response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile_complete = self._get_new_profile_complete_user_object()

        response2 = client.patch(
            reverse('django_sso_app_user:rest-detail', args=[new_incomplete_user.sso_app_profile.sso_id]),
            data=json.dumps(profile_complete),
            content_type='application/json'
        )
        print('RESP', response2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        new_incomplete_user.refresh_from_db()

        self.assertEqual(new_incomplete_user.username, profile_complete['username'])

        self.assertEqual(new_incomplete_user.sso_app_profile.first_name,
                         profile_complete['profile']['first_name'])

        self.assertEqual(new_incomplete_user.sso_app_profile.is_incomplete, False)

        invalid_profile_complete = self._get_new_profile_complete_user_object()

        response3 = client.patch(
            reverse('django_sso_app_user:rest-detail', args=[new_incomplete_user.sso_app_profile.sso_id]),
            data=json.dumps(invalid_profile_complete),
            content_type='application/json'
        )

        self.assertEqual(response3.status_code, status.HTTP_200_OK)

        new_incomplete_user.refresh_from_db()

        self.assertNotEqual(invalid_profile_complete['username'], new_incomplete_user.username)
