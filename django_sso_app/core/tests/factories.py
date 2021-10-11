import uuid as uuid_lib

import responses
from dateutil import tz

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.test import TestCase, Client

from allauth.account.adapter import get_adapter

import jwt
from http.cookies import SimpleCookie
from rest_framework.authtoken.models import Token

from django_sso_app.core.apps.emails.models import EmailAddress
from django_sso_app.core.apps.services.models import Service, Subscription
from django_sso_app.core.apps.groups.models import Group
from django_sso_app.core.apps.devices.utils import add_profile_device

import string
import random
from datetime import datetime

from faker import Faker

fake = Faker()
User = get_user_model()


class UserTestCase(TestCase):
    def _get_random_uuid(self):
        return str(uuid_lib.uuid4())

    def _get_random_string(self, length=20):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))

    def _get_random_pass(self, length=8):
        return self._get_random_string(length)

    def _get_random_username(self):
        return fake.user_name()

    def _get_random_email(self):
        return fake.ascii_safe_email()

    def _get_random_datetime(self, start_datetime=None):
        d = fake.date_time_between(start_date=start_datetime, end_date='+100y', tzinfo=tz.gettz('UTC'))
        return d.isoformat()

    def _get_random_birthdate(self, start_date='-99y', end_date='-18y'):
        d = fake.date_time_between(start_date=start_date, end_date=end_date)
        return d.strftime('%Y-%m-%d')

    def _get_client(self):
        return Client()

    def _get_allauth_adapter(self, request=None):
        return get_adapter(request)

    def _get_login_object(self, login, password):
        return {
            'login': login,
            'password': password,
            'fingerprint': self._get_random_string()
        }

    def _get_random_languagecode(self):
        L_CODES = ['en', 'it', 'fr', 'de']

        return random.choice(L_CODES)

    def _get_random_country(self):
        return self._get_random_languagecode().upper()

    def _get_random_latitude(self):
        return random.random() / 100

    def _get_random_longitude(self):
        return random.random() / 100

    def _get_new_profile_object(self, country='en', language='en', incomplete=False):
        from django_sso_app import app_settings

        obj = {}
        for f in app_settings.PROFILE_FIELDS:
            if f == 'birthdate':
                obj[f] = self._get_random_birthdate()
            elif f == 'expiration_date':
                obj[f] = self._get_random_datetime(start_datetime=datetime.now())
            elif f == 'picture':
                pass
            elif f == 'language':
                obj[f] = language or self._get_random_languagecode()
            elif f in ['country', 'country_of_birth']:
                obj[f] = country or self._get_random_country()
            elif f == 'latitude':
                obj[f] = self._get_random_latitude()
            elif f == 'longitude':
                obj[f] = self._get_random_longitude()
            elif f == 'gender':
                obj[f] = self._get_random_string(15)
            else:
                obj[f] = self._get_random_string()

        if incomplete:
            for f in app_settings.REQUIRED_PROFILE_FIELDS:
                obj[f] = None

        return obj

    def _get_new_profile_complete_user_object(self, username=None):
        return {
            'username': username or self._get_random_username(),
            'profile': self._get_new_profile_object()
        }

    def _get_new_invalid_profile_complete_user_object(self, username=None):
        from django_sso_app import app_settings

        profile_complete_object = self._get_new_profile_complete_user_object(username)
        profile_complete_object['profile'].pop(app_settings.REQUIRED_PROFILE_FIELDS[0])

        return profile_complete_object

    def _get_new_user_object(self, username=None, email=None, password=None, profile_object=None, incomplete=False):
        return {
            'username': username or self._get_random_username(),
            'email': email or self._get_random_email(),
            'password': password or self._get_random_pass(),
            'profile': profile_object or self._get_new_profile_object(incomplete=incomplete)
        }

    def _get_new_subscription_object(self, service_name=None, is_unsubscribed=False):
        domain_name = service_name or fake.domain_name()

        return {
            'service_url': 'http://{}'.format(domain_name),
            'is_unsubscribed': is_unsubscribed
        }

    def _get_new_group(self, name=None):

        group_name = name or self._get_random_string()

        return Group.objects.create(name=group_name)

    def _get_remote_user_object(self, uuid=None, username=None, email=None, password=None,
                                profile_object=None,
                                service_name=None,
                                service_subscribed=True,
                                group_name=None,
                                incomplete=False):
        from django_sso_app import app_settings

        user_uuid = uuid or self._get_random_uuid()
        user_object = self._get_new_user_object(username, email, password, profile_object, incomplete=incomplete)

        user_object['password'] = make_password(user_object['password'])

        user_object['sso_id'] = user_uuid
        user_object['sso_rev'] = random.randint(1, 100)

        user_object['url'] = app_settings.REMOTE_USER_URL.format(sso_id=user_uuid)

        user_object_profile_service = self._get_new_subscription_object(service_name, is_unsubscribed=not service_subscribed)

        user_object['profile']['subscriptions'] = [
            user_object_profile_service
        ]

        user_object['profile']['groups'] = [
            group_name or self._get_random_string()
        ]

        if incomplete:
            user_object['profile']['is_incomplete'] = True
            user_object['profile']['groups'] += [
                'incomplete'
            ]
            user_object['profile']['is_incomplete'] = True

        return user_object

    def _get_signup_object(self, username=None, email=None, referer=None, invalid=False):
        password = self._get_random_pass()

        obj = {
            'email': email or self._get_random_email(),
            'password1': password,
            'password2': password
        }

        if username is not None:
            obj['username'] = username

        if referer is not None:
            obj['referer'] = referer

        if invalid:
            obj.pop('email')

        return obj

    def _get_username_signup_object(self, username=None):
        return self._get_signup_object(username=username or self._get_random_username())

    def _get_invalid_signup_object(self):
        return self._get_signup_object(invalid=True)

    def _get_subscribe_signup_object(self, referer):
        return self._get_signup_object(referer=referer)

    def _get_new_service(self, name=None):
        domain_name = name or fake.domain_name()

        return Service.objects.create(service_url='http://{}'.format(domain_name), name=domain_name)

    def _get_new_user(self, username=None, email=None, password=None, service=None,
                      is_staff=False, is_superuser=False, incomplete=False):

        user = User(
            username=username or self._get_random_username(),
            email=email or self._get_random_email(),
            is_staff=is_staff,
            is_superuser=is_superuser
        )

        user.set_password(password or self._get_random_pass())

        if not is_staff and not is_superuser:
            _profile = self._get_new_profile_object(incomplete=incomplete)

            setattr(user, '__dssoa__profile__object', _profile)

            user.save()

            _user_email = EmailAddress.objects.create(user=user,
                                                      email=user.email,
                                                      primary=True,
                                                      verified=True)
        else:
            user.save()

        if service is not None:
            Subscription.objects.get_or_create(profile=user.sso_app_profile, service=service)

        return user

    def _get_new_staff_user(self, username=None, email=None, password=None):
        return self._get_new_user(username=username, email=email, password=password, is_staff=True)

    def _get_new_admin_user(self, username=None, email=None, password=None):
        return self._get_new_user(username=username, email=email, password=password, is_staff=True, is_superuser=True)

    def _get_new_incomplete_user(self, username=None, email=None, password=None):
        return self._get_new_user(username=username, email=email, password=password, incomplete=True)

    def _get_new_subscribed_user(self, service=None, username=None, email=None, password=None):
        subscribed_service = service or self._get_new_service()
        return self._get_new_user(service=subscribed_service, username=username, email=email, password=password)

    def _get_response_jwt_cookie(self, response):
        cookies = response.client.cookies.items()

        for (key, val) in cookies:
            if key == "jwt":
                return getattr(val, '_value')

    def _get_user_device(self, user, fingerprint=None):
        fp = fingerprint or self._get_random_string()

        return add_profile_device(user.sso_app_profile, fp)

    def _get_jwt(self, device, secret):
        from django_sso_app import app_settings

        secret = secret or device.apigw_jwt_secret

        return jwt.encode(
            device.get_jwt_payload(),
            secret,
            app_settings.JWT_ALGORITHM).decode('utf-8')

    def _get_jwt_cookie(self, device, secret=None):
        from django_sso_app import app_settings

        secret = secret or device.apigw_jwt_secret

        return SimpleCookie({
            app_settings.JWT_COOKIE_NAME: self._get_jwt(device, secret)
        })

    def _get_jwt_payload(self, sso_id=None, sso_rev=None, fingerprint=None):
        return {
            'id': random.randint(1, 1000),
            'fp': fingerprint or self._get_random_string(),
            'fingerprint': self._get_random_string(),
            'sso_id': sso_id or self._get_random_uuid(),
            'sso_rev': sso_rev or random.randint(0, 100)
        }

    def _get_valid_jwt(self, sso_id=None, sso_rev=None, fingerprint=None, secret=None):
        from django_sso_app import app_settings

        secret = secret or app_settings.TOKENS_JWT_SECRET

        valid_new_profile_jwt_payload = self._get_jwt_payload(sso_id, sso_rev, fingerprint)

        return jwt.encode(
            valid_new_profile_jwt_payload,
            secret,
            app_settings.JWT_ALGORITHM
        ).decode('utf-8')

    def _get_valid_jwt_cookie(self, sso_id=None, sso_rev=None, fingerprint=None, secret=None):
        from django_sso_app import app_settings

        return SimpleCookie({
            app_settings.JWT_COOKIE_NAME: self._get_valid_jwt(sso_id, sso_rev, fingerprint, secret=secret)
        })

    def _get_new_api_token(self, user):
        return Token.objects.create(user=user)

    def _get_new_api_token_headers(self, user):
        token = self._get_new_api_token(user)

        return {
            'content_type': 'application/json',
            'HTTP_AUTHORIZATION': 'Token {}'.format(token.key)
        }

    def _set_mocked_response(self, mocked_url, mocked_response, status=200, method='GET'):
        if method == 'POST':
            responses.add(responses.POST, mocked_url,
                          json=mocked_response, status=status)
        else:
            responses.add(responses.GET, mocked_url,
                          json=mocked_response, status=status)

    def _test_response_location(self, response, location):
        self.assertEqual(response['location'], location)

    def _test_response_path(self, response, path):
        self.assertEqual(response.request['PATH_INFO'], path)
