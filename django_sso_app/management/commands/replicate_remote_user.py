from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from django_sso_app.core.apps.users.utils import replicate_remote_user

User = get_user_model()


class Command(BaseCommand):
    help = 'Replicates a remote user'

    def add_arguments(self, parser):
        parser.add_argument('sso_id', type=str)

    def handle(self, *args, **options):
        sso_id = options['sso_id']

        new_user = replicate_remote_user(sso_id)

        self.stdout.write(self.style.SUCCESS('User "{}" replicated'.format(new_user)))
