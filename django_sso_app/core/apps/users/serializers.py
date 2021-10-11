import logging

from django.contrib.auth import get_user_model
from django import forms

from allauth.account.adapter import get_adapter
from rest_framework import serializers

from ...utils import set_session_key
from ... import app_settings
from ...permissions import is_staff
from ...serializers import AbsoluteUrlSerializer
from ..emails.models import EmailAddress
from ..profiles.models import Profile
from ..profiles.utils import update_profile
from ..profiles.serializers import ProfileSerializer
from ..services.models import Service
from .utils import create_local_user_from_object

User = get_user_model()

logger = logging.getLogger('django_sso_app')


class CheckUserExistenceSerializer(serializers.ModelSerializer):
    sso_id = serializers.SerializerMethodField(required=False)

    class Meta:
        model = User
        fields = ('sso_id',)
        read_only_fields = ('sso_id', )

    def get_sso_id(self, instance):
        return instance.sso_id


class UserRevisionSerializer(serializers.ModelSerializer):
    sso_id = serializers.SerializerMethodField(required=False)
    sso_rev = serializers.SerializerMethodField(required=False)

    class Meta:
        model = User
        read_only_fields = ('sso_id', 'sso_rev')
        fields = read_only_fields

    def get_sso_id(self, instance):
        return instance.sso_id

    def get_sso_rev(self, instance):
        return instance.sso_rev


class UserProfileSerializer(AbsoluteUrlSerializer):
    sso_id = serializers.CharField(required=False)
    sso_rev = serializers.IntegerField(required=False)

    subscriptions = serializers.SerializerMethodField(required=False)

    ssn = serializers.CharField(required='ssn' in app_settings.REQUIRED_PROFILE_FIELDS)
    phone = serializers.CharField(required='phone' in app_settings.REQUIRED_PROFILE_FIELDS)

    first_name = serializers.CharField(required='first_name' in app_settings.REQUIRED_PROFILE_FIELDS)
    last_name = serializers.CharField(required='last_name' in app_settings.REQUIRED_PROFILE_FIELDS,
                                      allow_null=True,
                                      allow_blank=True)

    description = serializers.CharField(required='description' in app_settings.REQUIRED_PROFILE_FIELDS,
                                        allow_null=True, allow_blank=True)
    picture = serializers.CharField(required='picture' in app_settings.REQUIRED_PROFILE_FIELDS, allow_null=True)
    birthdate = serializers.DateField(required='birthdate' in app_settings.REQUIRED_PROFILE_FIELDS,
                                      allow_null=True)
    country_of_birth = serializers.CharField(required='country_of_birth' in app_settings.REQUIRED_PROFILE_FIELDS)

    latitude = serializers.FloatField(required='latitude' in app_settings.REQUIRED_PROFILE_FIELDS)
    longitude = serializers.FloatField(required='longitude' in app_settings.REQUIRED_PROFILE_FIELDS)

    country = serializers.CharField(required='country' in app_settings.REQUIRED_PROFILE_FIELDS)
    address = serializers.CharField(required='address' in app_settings.REQUIRED_PROFILE_FIELDS, allow_null=True)

    language = serializers.CharField(required='language' in app_settings.REQUIRED_PROFILE_FIELDS,
                                     allow_null=True)

    alias = serializers.CharField(required='alias' in app_settings.REQUIRED_PROFILE_FIELDS,
                                  allow_null=True)

    gender = serializers.CharField(required='gender' in app_settings.REQUIRED_PROFILE_FIELDS,
                                   allow_null=True)

    company_name = serializers.CharField(required='company_name' in app_settings.REQUIRED_PROFILE_FIELDS)

    class Meta:
        model = Profile
        read_only_fields = (
            'url',
            'created_at',
            'sso_id', 'sso_rev',
            'subscriptions',
            'is_unsubscribed',
            'groups')
        fields = read_only_fields + app_settings.PROFILE_FIELDS

    def get_subscriptions(self, instance):
        serialized = []
        if app_settings.BACKEND_ENABLED:
            for el in instance.subscriptions.all():
                serialized.append({
                    'service_url': el.service.service_url,
                    'is_unsubscribed': getattr(el, 'is_unsubscribed', False)
                })
        return serialized


class UserSerializer(AbsoluteUrlSerializer):
    sso_id = serializers.SerializerMethodField(required=False)
    sso_rev = serializers.SerializerMethodField(required=False)
    email_verified = serializers.SerializerMethodField(required=False)
    groups = serializers.SerializerMethodField(required=False)
    profile = ProfileSerializer(required=False, source='sso_app_profile')

    class Meta:
        model = User
        read_only_fields = (
            'url',
            'sso_id', 'sso_rev',
            'date_joined', 'last_login',
            'is_active', 'email_verified',
            'groups')
        fields = read_only_fields + app_settings.USER_FIELDS + ('password', 'profile')

    def get_sso_id(self, instance):
        return instance.sso_id

    def get_sso_rev(self, instance):
        return instance.sso_rev

    def get_email_verified(self, user):
        if app_settings.BACKEND_ENABLED:
            try:
                verified_email_addresses = user.emailaddress_set.filter(email=user.email, verified=True)
                return verified_email_addresses.count() > 0

            except:
                logger.info('user "{}" has no verified emails'.format(user))
                return False

        return True

    def get_groups(self, instance):
        groups = list(instance.groups.values_list('name', flat=True))

        return groups

    def to_representation(self, obj):
        # get the original representation
        ret = super(UserSerializer, self).to_representation(obj)
        request = self.context.get('request', None)

        if request is not None:
            # remove field if password if not asked
            requesting_user = request.user
            requesting_user_is_staff = is_staff(requesting_user)
            is_same_user = requesting_user.sso_id == ret['sso_id']

            with_password = request.query_params.get('with_password',
                                                     not app_settings.BACKEND_HIDE_PASSWORD_FROM_USER_SERIALIZER)

            show_user_protected_informations = False
            hide_password = True

            if requesting_user_is_staff or is_same_user:
                show_user_protected_informations = True

            if show_user_protected_informations:
                logger.info('show protected informations')
                if requesting_user_is_staff and with_password:
                    hide_password = False
            else:
                ret.pop('email', None)

                ret['profile'].pop('email', None)
                ret['profile'].pop('first_name', None)
                ret['profile'].pop('last_name', None)
                ret['profile']['_partial'] = True

            if hide_password:
                ret.pop('password', None)
                ret['_partial'] = True

        # return the modified representation
        return ret

    def update(self, instance, validated_data):
        user = instance
        request = self.context.get("request")
        requesting_user = request.user
        adapter = get_adapter(request=request)

        requesting_user_is_staff = is_staff(requesting_user)

        skip_confirmation = request.GET.get('skip_confirmation', None)
        must_confirm_email = True
        if requesting_user_is_staff and skip_confirmation is not None:
            must_confirm_email = False

        password_is_hashed = request.query_params.get('password_is_hashed', None)

        new_email = validated_data.get('email', None)
        new_password = validated_data.get('password', None)
        new_username = validated_data.get('username', None)
        updated_profile = request.data.get('profile', None)

        logger.info('User "{}" wants to update user "{}"'.format(requesting_user, user))

        if (new_email is not None) and (new_email != user.email):

            logger.info('User "{}" is changing email for user "{}"'.format(requesting_user,
                                                                           user))

            adapter.validate_unique_email(new_email)

            created_email = EmailAddress.objects.add_email(request, user,
                                                           new_email,
                                                           confirm=must_confirm_email)

            logger.info('A new user EmailAddress for user "{}" has been created ({})'.format(user,
                                                                                             created_email.id))

            if must_confirm_email:
                logger.info('"{}" must confirm email "{}"'.format(user, new_email))

                user.sso_app_profile.update_rev(True)

            else:
                logger.info('confirming email "{}"'.format(new_email))
                created_email.verified = True
                created_email.set_as_primary(conditional=False)

                adapter.update_user_email(user, new_email)

        if new_password is not None:
            logger.info('user "{}" is changing password for user "{}"'.format(requesting_user,
                                                                              user))

            if password_is_hashed:
                logger.info('password is hashed')
                user.password = new_password
            else:
                logger.info('password is plain')
                user.set_password(new_password)

            set_session_key(request, '__dssoa__user_password_updated', True)

            user.save()

        if new_username is not None and not user.sso_app_profile.completed_at:
            logger.info('user "{}" is changing username for user "{}"'.format(requesting_user,
                                                                              user))

            try:
                adapter.clean_username(new_username)

            except forms.ValidationError:
                logger.warning('Can\'t set username as "{}" for user "{}"'.format(new_username, user))
                raise

            else:
                adapter.update_user_username(user, new_username)

        if updated_profile is not None:
            logger.info('user "{}" is updating profile for user "{}"'.format(requesting_user,
                                                                             user))

            # setting new_user profile serializer field
            setattr(user, 'sso_app_profile', update_profile(user.sso_app_profile, updated_profile))

        return user

    def get_cleaned_data(self):
        return self.validated_data

    @property
    def cleaned_data(self):
        return self.validated_data


class NewUserSerializer(UserSerializer):
    profile = UserProfileSerializer(required=False)

    def create(self, validated_data):
        request = self.context.get('request')
        requesting_user = request.user

        requesting_user_is_staff = is_staff(requesting_user)
        skip_confirmation = request.GET.get('skip_confirmation', None)
        must_confirm_email = True
        password_is_hashed = request.query_params.get('password_is_hashed', None)

        if password_is_hashed:
            new_password = validated_data.pop('password', None)
        else:
            new_password = validated_data.get('password', None)
            validated_data.update(password1=new_password)
            validated_data.update(password2=new_password)

        assert (new_password is not None)

        # start creating new user
        new_user = None
        try:
            logger.info('User "{}" wants to create new user "{}"'.format(requesting_user, validated_data))

            if requesting_user_is_staff and skip_confirmation is not None:
                must_confirm_email = False

            new_user = create_local_user_from_object(validated_data, verified=(not must_confirm_email))
            new_user_profile_validated_object = validated_data.get('profile', {})

            # setting new_user profile serializer field
            setattr(new_user, 'profile', update_profile(new_user.sso_app_profile, new_user_profile_validated_object))

            if password_is_hashed:
                logger.info('New user password is hashed')
                new_user.password = new_password
                new_user.save()

            try:
                new_user_profile_request_object = request.data.get('profile', {})
                profile_object_subscriptions = new_user_profile_request_object.get('subscriptions', [])

                logger.info('Subscripting new user to services "{}"'.format(profile_object_subscriptions))

                if len(profile_object_subscriptions) > 0:
                    for new_subscription in profile_object_subscriptions:
                        new_subscription_service_name = new_subscription.get('service').get('name')
                        service = Service.objects.get(name=new_subscription_service_name)
                        service.subscribe(new_user.get_sso_app_profile())

            except Exception:
                logger.exception('Error subscribing service on user creation')
                raise serializers.ValidationError('Error subscribing service')

            if must_confirm_email:
                logger.info('Sending confirmation email to new user "{}"'.format(new_user))
                new_user_email_address = new_user.emailaddress_set.last()
                new_user_email_address.send_confirmation(request=request, signup=True)

            return new_user

        # delete creating user model if any exception occurred
        except Exception as e:
            logger.exception('Error creating new user "{}"'.format(e))

            if new_user is not None:
                new_user.delete()

            raise


class SuccessfullLoginResponseSerializer(serializers.Serializer):
    """
    Login success response serializer
    """
    token = serializers.CharField()
    user = UserSerializer()
    redirect_url = serializers.CharField(required=False)


class SuccessfullLogoutResponseSerializer(serializers.Serializer):
    """
    Logout success response serializer
    """
    redirect_url = serializers.CharField(required=False)
