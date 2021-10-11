import logging
import json
import responses

from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse

from rest_framework import status

from django_sso_app.core.tests.factories import UserTestCase

from .... import app_settings
from ...emails.models import EmailAddress
from ..models import RequestForCredentialsEventListener
from ..tasks import create_users_by_events

logger = logging.getLogger('django_sso_app')
User = get_user_model()
ELASTICSEARCH_INDEX_URL = app_settings.EVENTS_HOST + '/{}/_search'.format(app_settings.EVENTS_INDEX)


class EventTestCase(UserTestCase):
    @responses.activate
    def test_can_create_users_by_event_objects(self):
        email_verified = True
        default_password = 'password1234'
        rfc_event_listener = RequestForCredentialsEventListener(confirm_email=email_verified,
                                                                first_name_field='name',
                                                                default_password=default_password)
        rfc_event_listener.save()

        new_user_email = 'pinco@example.com'
        new_user_first_name = 'Pinco'
        event_group_name = 'q-hack40-cps-bs'
        event_password = 'qhack'

        _es_response = """{
          "took" : 1,
          "timed_out" : false,
          "_shards" : {
            "total" : 1,
            "successful" : 1,
            "skipped" : 0,
            "failed" : 0
          },
          "hits" : {
            "total" : {
              "value" : 1,
              "relation" : "eq"
            },
            "max_score" : null,
            "hits" : [
              {
                "_index" : "events_private",
                "_type" : "_doc",
                "_id" : "c59a89334cc15b9f89ace22ef30006af",
                "_score" : null,
                "_source" : {
                  "@timestamp" : "2021-03-31T14:23:08.307Z",
                  "doc" : {
                    "type" : "request_for_credentials",
                    "group" : "{{event_group_name}}",
                    "stack" : "events",
                    "captcha_is_valid" : true,
                    "sso_id" : "form",
                    "name" : "{{new_user_first_name}}",
                    "ip" : "172.19.0.1",
                    "position" : {
                      "lon" : "12.56738",
                      "lat" : "41.871939999999995"
                    },
                    "note" : "...",
                    "email" : "{{new_user_email}}",
                    "timestamp" : 1.617200588307E9
                  }
                },
                "sort" : [
                  1617200588307
                ]
              }
            ]
          }
        }
        """.replace('{{new_user_email}}', new_user_email) \
            .replace('{{new_user_first_name}}', new_user_first_name) \
            .replace('{{event_group_name}}', event_group_name) \
            .replace('{{event_password}}', event_password)

        es_response = json.loads(_es_response)

        mocked_url = ELASTICSEARCH_INDEX_URL
        self._set_mocked_response(mocked_url, es_response, method='POST')

        new_users_created = create_users_by_events()
        self.assertEqual(new_users_created, 1)

        new_users = User.objects.filter(email=new_user_email)
        new_user = new_users.first()
        self.assertEqual(new_user.email, new_user_email)
        self.assertEqual(new_user.sso_app_profile.first_name, new_user_first_name)
        self.assertEqual(new_users.count(), 1)

        email_addresses = EmailAddress.objects.filter(email=new_user_email)
        email_address = email_addresses.first()
        self.assertEqual(email_addresses.count(), 1)
        self.assertEqual(email_address.verified, email_verified)
        self.assertEqual(email_address.primary, True)

        # confirmation email
        if not email_verified:
            self.assertEqual(len(mail.outbox), 1)
            cofirmation_message = mail.outbox[0]
            recipients = cofirmation_message.recipients()
            self.assertIn(new_user_email, recipients, 'user email not in recipients')

        # check profile groups
        self.assertEqual(new_user.sso_app_profile.groups.filter(name=event_group_name).count(), 1)

        if default_password is not None:
            self.assertEqual(new_user.has_usable_password(), True)

        # check user can login
        client = self._get_client()
        response = client.post(
            reverse('account_login'),
            data=self._get_login_object(new_user_email, default_password)
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '/')
        self.assertIsNotNone(self._get_response_jwt_cookie(response), 'response has no jwt cookie')

    @responses.activate
    def test_can_not_create_users_by_event_objects_if_exists(self):
        rfc_event_listener = RequestForCredentialsEventListener(confirm_email=False,
                                                                first_name_field='name')
        rfc_event_listener.save()

        new_user_email = 'pinco@example.com'
        new_user_first_name = 'Pinco'
        event_group_name = 'q-hack40-cps-bs'

        new_pass = self._get_random_pass()
        previous_user = self._get_new_user(password=new_pass, username=new_user_first_name, email=new_user_email)
        print('previous', previous_user)

        _es_response = """{
          "took" : 1,
          "timed_out" : false,
          "_shards" : {
            "total" : 1,
            "successful" : 1,
            "skipped" : 0,
            "failed" : 0
          },
          "hits" : {
            "total" : {
              "value" : 1,
              "relation" : "eq"
            },
            "max_score" : null,
            "hits" : [
              {
                "_index" : "events_private",
                "_type" : "_doc",
                "_id" : "c59a89334cc15b9f89ace22ef30006af",
                "_score" : null,
                "_source" : {
                  "@timestamp" : "2021-03-31T14:23:08.307Z",
                  "doc" : {
                    "type" : "request_for_credentials",
                    "group" : "{{event_group_name}}",
                    "stack" : "events",
                    "captcha_is_valid" : true,
                    "sso_id" : "form",
                    "name" : "{{new_user_first_name}}",
                    "ip" : "172.19.0.1",
                    "position" : {
                      "lon" : "12.56738",
                      "lat" : "41.871939999999995"
                    },
                    "note" : "...",
                    "email" : "{{new_user_email}}",
                    "timestamp" : 1.617200588307E9
                  }
                },
                "sort" : [
                  1617200588307
                ]
              }
            ]
          }
        }
        """.replace('{{new_user_email}}', new_user_email).replace('{{new_user_first_name}}', new_user_first_name).replace('{{event_group_name}}', event_group_name)
        es_response = json.loads(_es_response)
        mocked_url = ELASTICSEARCH_INDEX_URL
        self._set_mocked_response(mocked_url, es_response, method='POST')

        new_users_created = create_users_by_events()
        self.assertEqual(new_users_created, 0)

        users = User.objects.filter(email=new_user_email)
        self.assertEqual(users.count(), 1)
