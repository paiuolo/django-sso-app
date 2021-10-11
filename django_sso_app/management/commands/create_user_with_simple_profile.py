from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from django_sso_app.core.apps.users.utils import create_local_user_from_object

User = get_user_model()


class Command(BaseCommand):
    help = 'Loads an external simple user'

    def add_arguments(self, parser):
        parser.add_argument('sso_id', type=str)
        parser.add_argument('username', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('groups', type=str, nargs='*', default=[])

    def handle(self, *args, **options):
        sso_id = options['sso_id']
        username = options['username']
        email = options['email']
        groups = options['groups']
        groups_count = len(groups)

        try:
            validate_email(email)
        except ValidationError as e:
            self.stdout.write(self.style.ERROR(e.message))
            return

        if User.objects.filter(username=username).count() > 0:
            self.stdout.write(self.style.ERROR('User with username "{}" already present'.format(username)))
            return
        if User.objects.filter(email=email).count() > 0:
            self.stdout.write(self.style.ERROR('User with email "{}" already present'.format(email)))
            return

        self.stdout.write(self.style.NOTICE('Creating user: {} {} {} with {} groups: {}'.format(
            sso_id,
            username,
            email,
            groups_count,
            groups)))

        new_user = create_local_user_from_object({'username': username,
                                                  'email': email,
                                                  'sso_id': sso_id,
                                                  'sso_rev': 0},
                                                 verified=True)

        for group_name in groups:
            new_user.sso_app_profile.add_to_group(group_name, creating=True)

        self.stdout.write(self.style.SUCCESS('New user "{}" created'.format(new_user)))
