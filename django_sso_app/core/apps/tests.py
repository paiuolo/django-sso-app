import os
import json
import shutil

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import auth

from rest_framework import status
from rest_framework.test import APITestCase

from ..apps.emails.models import EmailAddress

User = get_user_model()


class APITestFactory(APITestCase):
    def setUp(self):
        self.user_username = 'pippo'
        self.user_email = 'pippo@example.com'
        self.user_password = 'password'
        self.user = User.objects.create(username=self.user_username, email=self.user_email)
        self.user.set_password(self.user_password)
        self.user.save()

        self.user_email = EmailAddress.objects.create(user=self.user,
                                                      email=self.user_email,
                                                      primary=True,
                                                      verified=True)

        self.valid_login = {
            'login': self.user_username,
            'password': self.user_password,
            'fingerprint': '123456'
        }

    def tearDown(self):
        shutil.rmtree(self.user_folder_path, ignore_errors=True)

    def perform_user_login(self):
        response = self.client.post(
            reverse('rest_login'),
            data=json.dumps(self.valid_login),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        return response
