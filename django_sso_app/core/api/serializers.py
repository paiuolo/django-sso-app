import logging

from django.utils.translation import activate as activate_translation
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers, exceptions
from rest_framework.exceptions import ValidationError

from allauth.account import app_settings as allauth_settings
from allauth.utils import get_username_max_length

from ..apps.emails.models import EmailAddress
from ..apps.groups.models import Group
from ..forms import LoginForm, SignupForm
from .. import app_settings

logger = logging.getLogger('django_sso_app')


class LoginSerializer(serializers.Serializer):
    form_class = LoginForm

    login = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})
    fingerprint = serializers.CharField(required=False, allow_null=True)

    """
    def validate_fingerprint(self, fingerprint):
        if fingerprint is None:
            msg = _('Must include "fingerprint"')
            raise exceptions.ValidationError(msg)

        return fingerprint
    """


class BaseSignupSerializer(serializers.Serializer):
    form_class = SignupForm

    username = serializers.CharField(
        max_length=get_username_max_length(),
        min_length=allauth_settings.USERNAME_MIN_LENGTH,
        required=allauth_settings.USERNAME_REQUIRED
    )
    email = serializers.EmailField(required=allauth_settings.EMAIL_REQUIRED)

    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    referer = serializers.CharField(required=False)

    fingerprint = serializers.CharField(required=False, allow_null=True)

    groups = serializers.ListField(child=serializers.CharField(), required=False)


if app_settings.BACKEND_SIGNUP_MUST_FILL_PROFILE:
    class SignupSerializer(BaseSignupSerializer):
        first_name = serializers.CharField(required='first_name' in app_settings.REQUIRED_PROFILE_FIELDS)
        last_name = serializers.CharField(required='last_name' in app_settings.REQUIRED_PROFILE_FIELDS,
                                          allow_null=True,
                                          allow_blank=True)

        description = serializers.CharField(required='description' in app_settings.REQUIRED_PROFILE_FIELDS,
                                            allow_null=True, allow_blank=True)
        picture = serializers.CharField(required='picture' in app_settings.REQUIRED_PROFILE_FIELDS, allow_null=True)
        birthdate = serializers.DateField(required='birthdate' in app_settings.REQUIRED_PROFILE_FIELDS,
                                          allow_null=True)

        latitude = serializers.FloatField(required='latitude' in app_settings.REQUIRED_PROFILE_FIELDS,
                                          allow_null=True)
        longitude = serializers.FloatField(required='longitude' in app_settings.REQUIRED_PROFILE_FIELDS,
                                           allow_null=True)

        country = serializers.CharField(required='country' in app_settings.REQUIRED_PROFILE_FIELDS, allow_null=True)
        country_of_birth = serializers.CharField(required='country_of_birth' in app_settings.REQUIRED_PROFILE_FIELDS,
                                                 allow_null=True)
        address = serializers.CharField(required='address' in app_settings.REQUIRED_PROFILE_FIELDS, allow_null=True)

        language = serializers.CharField(required='language' in app_settings.REQUIRED_PROFILE_FIELDS, allow_null=True)

        alias = serializers.CharField(required='alias' in app_settings.REQUIRED_PROFILE_FIELDS, allow_null=True)

        gender = serializers.CharField(required='gender' in app_settings.REQUIRED_PROFILE_FIELDS, allow_null=True)

        company_name = serializers.CharField(required='company_name' in app_settings.REQUIRED_PROFILE_FIELDS, allow_null=True)

else:
    class SignupSerializer(BaseSignupSerializer):
        pass


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        value = super(PasswordResetSerializer, self).validate_email(value)
        saved_email = EmailAddress.objects.get(email=value)
        if not saved_email.verified:
            raise ValidationError(
                _('E-mail address not verified: %(value)s'),
                code='invalid',
                params={'value': value},
            )

        user = saved_email.user
        user_language = user.language
        logger.info('Rendering PasswordResetSerializer mail for {0} with language {1}'.format(user, user_language))
        activate_translation(user_language)

        return value


class PasswordResetFromKeySerializer(serializers.Serializer):
    uidb36 = serializers.CharField()
    key = serializers.CharField()
    password1 = serializers.CharField()
    password2 = serializers.CharField()


class AddEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordChangeSerializer(serializers.Serializer):
    oldpassword = serializers.CharField()
    password1 = serializers.CharField()
    password2 = serializers.CharField()


class PasswordSetSerializer(serializers.Serializer):
    password1 = serializers.CharField()
    password2 = serializers.CharField()
