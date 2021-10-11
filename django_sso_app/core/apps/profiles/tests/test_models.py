from django.contrib.auth import get_user_model

from django_sso_app.core.tests.factories import UserTestCase


class ProfileTestCase(UserTestCase):

    def test_profile_field_update_updates_rev(self):
        """
        User update updates user revision
        """
        user = self._get_new_user()
        profile = user.sso_app_profile

        profile_rev = profile.sso_rev

        profile.country = 'RU'
        profile.save()

        profile.refresh_from_db()

        self.assertEqual(profile.sso_rev, profile_rev + 1)

    def test_django_user_email_update_updates_profile_django_user_email(self):
        User = get_user_model()

        user = self._get_new_user()
        profile = user.sso_app_profile

        profile_rev = profile.sso_rev

        self.assertEqual(user.email, profile.django_user_email)

        user = User.objects.get(username=user.username)
        user.email = self._get_random_email()
        user.save()

        profile.refresh_from_db()

        self.assertEqual(profile.django_user_email, user.email)
        self.assertEqual(profile.sso_rev, profile_rev + 1)

    def test_django_user_username_update_updates_profile_django_user_username(self):
        User = get_user_model()

        user = self._get_new_user()
        profile = user.sso_app_profile

        profile_rev = profile.sso_rev

        self.assertEqual(user.username, profile.django_user_username)

        user = User.objects.get(username=user.username)
        user.username = self._get_random_username()
        user.save()

        profile.refresh_from_db()

        self.assertEqual(profile.django_user_username, user.username)
        self.assertEqual(profile.sso_rev, profile_rev + 1)
