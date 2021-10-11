from django.contrib.auth import get_user_model

from django_sso_app.core.tests.factories import UserTestCase
from django_sso_app.core.apps.emails.models import EmailAddress

User = get_user_model()


class TestEmailAddress(UserTestCase):

    def test_user_email_deletes_other_user_emails_when_primary_and_verified(self):
        user = self._get_new_user()

        self.assertEqual(user.emailaddress_set.count(), 1)

        new_email = EmailAddress.objects.create(user=user, email=self._get_random_email())

        self.assertEqual(user.emailaddress_set.count(), 2)

        new_email.primary = True
        new_email.verified = True
        new_email.save()

        self.assertEqual(user.emailaddress_set.count(), 1, 'other user email not confirmed')

    def test_user_can_have_only_one_not_validated_email(self):
        user = self._get_new_user()

        self.assertEqual(user.emailaddress_set.count(), 1)

        _new_email = EmailAddress.objects.create(user=user, email=self._get_random_email(), verified=False)

        self.assertEqual(user.emailaddress_set.count(), 2)

        new_email2 = EmailAddress.objects.create(user=user, email=self._get_random_email(), verified=False)

        self.assertEqual(user.emailaddress_set.count(), 2)

        new_email2.primary = True
        new_email2.verified = True
        new_email2.save()

        self.assertEqual(user.emailaddress_set.count(), 1, 'other user email not confirmed')
