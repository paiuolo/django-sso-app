from django_sso_app.core.tests.factories import UserTestCase

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test.utils import override_settings

from rest_framework import status


User = get_user_model()


class GroupTestCase(UserTestCase):
    @override_settings(DJANGO_SSO_APP_DEFAULT_USER_GROUPS=['group1', 'group2'])
    def test_user_groups_assigned_on_login(self):
        new_pass = self._get_random_pass()
        new_user = self._get_new_user(password=new_pass)

        new_group = self._get_new_group('group3')
        new_user.add_to_group(new_group)

        user_groups_before_login = new_user.groups.all()
        self.assertEqual(user_groups_before_login.count(), 3)

        client = self._get_client()
        response = client.post(
            reverse('account_login'),
            data=self._get_login_object(new_user.email, new_pass)
        )
        print('RES00', response)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        user_groups_after_login = new_user.groups.all()

        self.assertEqual(list(map(lambda x: x.name, user_groups_before_login)),
                         list(map(lambda x: x.name, user_groups_after_login)))

        response2 = client.post(
            reverse('account_logout')
        )

        self.assertEqual(self._get_response_jwt_cookie(response2), '', 'api logout keeps jwt cookie')

