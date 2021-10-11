from django_sso_app.core.tests.factories import UserTestCase


class UserModelTestCase(UserTestCase):

    def test_django_superuser_user_creation_creates_sso_app_profile_with_sso_id_equals_to_username(self):
        admin_user_username = self._get_random_username()
        admin_user = self._get_new_admin_user(username=admin_user_username)

        self.assertEqual(admin_user.sso_id, admin_user.username)

    def test_django_staff_user_creation_creates_sso_app_profile_with_sso_id_equals_to_username(self):
        staff_user_username = self._get_random_username()
        staff_user = self._get_new_staff_user(username=staff_user_username)

        self.assertEqual(staff_user.sso_id, staff_user.username)
