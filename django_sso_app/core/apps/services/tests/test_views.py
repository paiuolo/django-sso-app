import json

import jwt
from django.urls import reverse
from rest_framework import status

from ...users.tests.test_views import UserTestCase
from ..models import Service


class TestSubscriptions(UserTestCase):

    def test_user_can_list_subscriptions(self):
        new_service = self._get_new_service()
        new_pass = self._get_random_pass()
        new_user = self._get_new_subscribed_user(service=new_service, password=new_pass)

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(new_user.email, new_pass)),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response2 = client.get(
            reverse('django_sso_app_service:rest-subscription-list'),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response2.data['results']), 1)
        self.assertEqual(response2.data['results'][0].get('service').get('service_url'), new_service.service_url)

    def test_user_can_retrieve_subscription(self):
        new_service = self._get_new_service()
        new_pass = self._get_random_pass()
        new_user = self._get_new_subscribed_user(service=new_service, password=new_pass)

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(new_user.email, new_pass)),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_service_subscription = new_user.sso_app_profile.subscriptions.first()

        response2 = client.get(
            reverse('django_sso_app_service:rest-subscription-detail', args=(new_service_subscription.id,)),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data.get('is_unsubscribed'), False)


class TestServices(UserTestCase):

    def test_user_can_list_services(self):
        new_service = self._get_new_service()
        new_pass = self._get_random_pass()
        new_user = self._get_new_subscribed_user(service=new_service, password=new_pass)

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(new_user.email, new_pass)),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response2 = client.get(
            reverse('django_sso_app_service:rest-list'),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response2.data['results']), Service.objects.count())

    def test_user_can_retrieve_service(self):
        new_service = self._get_new_service()
        new_pass = self._get_random_pass()
        new_user = self._get_new_subscribed_user(service=new_service, password=new_pass)

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(new_user.email, new_pass)),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response2 = client.get(
            reverse('django_sso_app_service:rest-detail', args=(new_service.id, )),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data.get('service_url'), new_service.service_url)

    def test_user_can_not_subscribe_profile_to_service_twice(self):
        new_service = self._get_new_service()
        new_pass = self._get_random_pass()
        new_user = self._get_new_subscribed_user(service=new_service, password=new_pass)

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(new_user.email, new_pass)),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response2 = client.post(
            reverse('django_sso_app_service:rest-subscription', args=(new_service.id, )),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response2.data, 'Already subscribed.')

    def test_user_can_subscribe_to_service_with_rev_incremented_and_devices_deleted(self):
        new_service = self._get_new_service()
        new_pass = self._get_random_pass()
        new_user = self._get_new_user(password=new_pass)

        new_user_profile = new_user.sso_app_profile
        first_rev = new_user_profile.sso_rev

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(new_user.email, new_pass)),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        first_devices = new_user_profile.devices.all()
        first_devices_ids = [x.id for x in first_devices]

        response2 = client.post(
            reverse('django_sso_app_service:rest-subscription', args=(new_service.id, )),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        new_user_profile.refresh_from_db()

        self.assertEqual(response2.data, 'Successfully subscribed.')

        new_user_profile.refresh_from_db()
        second_rev = new_user_profile.sso_rev

        self.assertEqual(second_rev, first_rev+1, 'rev not incremented')

        response3 = client.get(
            reverse('django_sso_app_service:rest-list'),
            content_type='application/json'
        )

        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response3.data['results']), Service.objects.count())

        jwt_cookie2 = self._get_response_jwt_cookie(response)

        unverified_payload2 = jwt.decode(jwt_cookie2, None, False)

        self.assertEqual(unverified_payload2.get('sso_rev'), second_rev, 'cookie rev NOT changed after login')

        second_devices = new_user_profile.devices.all()
        second_devices_ids = [x.id for x in second_devices]

        self.assertEqual(len(second_devices), 1)
        self.assertNotEqual(first_devices_ids, second_devices_ids)

    def test_user_can_unsubscribe_profile_from_service_with_rev_incremented(self):
        new_service = self._get_new_service()
        new_pass = self._get_random_pass()
        new_user = self._get_new_subscribed_user(service=new_service, password=new_pass)

        new_user_profile = new_user.sso_app_profile
        first_rev = new_user_profile.sso_rev

        client = self._get_client()
        response = client.post(
            reverse('rest_login'),
            data=json.dumps(self._get_login_object(new_user.email, new_pass)),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response2 = client.post(
            reverse('django_sso_app_service:rest-unsubscription', args=(new_service.id, )),
            data=json.dumps({
                'password': new_pass
            }),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data, 'Successfully unsubscribed.')

        new_user_profile.refresh_from_db()
        second_rev = new_user_profile.sso_rev

        self.assertEqual(second_rev, first_rev+1, 'rev not incremented on service unsubscription')

        jwt_cookie = self._get_response_jwt_cookie(response2)
        self.assertIsNotNone(jwt_cookie, 'no new jwt received')

        unverified_payload = jwt.decode(jwt_cookie, None, False)

        self.assertEqual(unverified_payload.get('sso_rev'), second_rev, 'rev NOT updated in JWT')

    def test_staff_user_can_subscribe_profile_to_service_with_profile_rev_incremented(self):
        new_service = self._get_new_service()
        new_pass = self._get_random_pass()
        new_user = self._get_new_user(password=new_pass)
        new_user_profile = new_user.sso_app_profile

        new_staff_user = self._get_new_staff_user()

        first_rev = new_user_profile.sso_rev

        client = self._get_client()
        response = client.post(
            reverse('django_sso_app_service:rest-subscription', args=(new_service.id, )),
            data=json.dumps({'sso_id': str(new_user_profile.sso_id)}),
            **self._get_new_api_token_headers(new_staff_user)
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, 'Successfully subscribed.')

        new_user_profile.refresh_from_db()
        second_rev = new_user_profile.sso_rev

        self.assertEqual(second_rev, first_rev+1, 'rev not incremented on service subscription')

