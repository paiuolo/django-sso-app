from django.core.management.base import BaseCommand  #, CommandError
from django.contrib.auth import get_user_model

from django_sso_app.core.apps.devices.utils import remove_all_profile_devices

User = get_user_model()


class Command(BaseCommand):
    help = 'Deletes all profiles devices'

    def handle(self, *args, **options):
        users = User.objects.all()
        users_count = users.count()
        updated_users = 0
        parsed_users = 0
        devices_count = 0
        deleted_devices = 0

        for user in users:
            try:
                profile_devices_count = user.sso_app_profile.devices.count()
                devices_count += profile_devices_count
                deleted_profile_devices_count = remove_all_profile_devices(user.get_sso_app_profile())

                if deleted_profile_devices_count > 0:
                    updated_users += 1
                    deleted_devices += deleted_profile_devices_count

                    self.stdout.write(
                        self.style.SUCCESS('Deleted {}/{} user devices for "{}"'.format(profile_devices_count,
                                                                                        deleted_profile_devices_count,
                                                                                        user)))

            except Exception as e:
                self.stdout.write(self.style.ERROR('Error "{}" deleting devices for "{}"'.format(e, user)))

            parsed_users += 1
            self.stdout.write(self.style.SUCCESS('{}/{}'.format(parsed_users, users_count)))

        self.stdout.write(self.style.SUCCESS('Updated {}/{} profiles'.format(users_count, updated_users)))
        self.stdout.write(self.style.SUCCESS('Deleted {}/{} devices'.format(deleted_devices, devices_count)))
