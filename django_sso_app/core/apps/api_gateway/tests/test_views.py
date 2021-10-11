import json

import jwt
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from rest_framework import status

from django_sso_app.core.tests.factories import UserTestCase

User = get_user_model()


class TestApiGateway(UserTestCase):

    def check_apigateway_is_enabled(self):
        pass
