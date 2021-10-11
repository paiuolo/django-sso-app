from django.core.management.base import BaseCommand  # , CommandError
from django.contrib.auth import get_user_model

from django_sso_app.core.apps.api_gateway.utils import get_profile_apigw_consumer_id  # , delete_apigw_consumer

User = get_user_model()


class Command(BaseCommand):
    help = 'Restores apigateway consumer by username'

    def add_arguments(self, parser):
        parser.add_argument('username', nargs='+', type=str)

    def handle(self, *args, **options):
        # for poll_id in options['poll_ids']:
        #     try:
        #         poll = Poll.objects.get(pk=poll_id)
        #     except Poll.DoesNotExist:
        #         raise CommandError('Poll "%s" does not exist' % poll_id)
        usernames = options['username']
        users = User.objects.filter(username__in=usernames)
        users_count = users.count()
        updated_users = 0

        for username in usernames:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR('User "{}" does not exist'.format(username)))
                continue

            try:
                consumer_id = get_profile_apigw_consumer_id(user.sso_app_profile, True)
                updated_users += 1
                self.stdout.write(self.style.SUCCESS('{}/{} "{}"'.format(updated_users, users_count, consumer_id)))

            except Exception as e:
                self.stdout.write(self.style.ERROR('Error "{}" restoring apigateway consumer for "{}"'.format(e, user)))

                # delete_apigw_consumer(user.sso_app_profile)

        self.stdout.write(self.style.SUCCESS('Restored {}/{} users'.format(updated_users, users_count)))
