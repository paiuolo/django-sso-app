import logging

from django.forms import CharField, DateField, FloatField, HiddenInput

from allauth.account.forms import (LoginForm as allauth_LoginForm,
                                   SignupForm as allauth_SignupForm)
from allauth.account.adapter import get_adapter
from allauth.account import app_settings as allauth_app_settings

from .apps.emails.models import EmailAddress
from .apps.services.models import Service
from .apps.groups.models import Group

from .utils import get_random_fingerprint
from . import app_settings

logger = logging.getLogger('django_sso_app')


SIGNUP_FORM_FIELDS = app_settings.USER_FIELDS + (
    'email2',  # ignored when not present
    'password1',
    'password2'  # ignored when not present
)


class LoginForm(allauth_LoginForm):
    fingerprint = CharField(label='fingerprint', max_length=255, required=False, widget=HiddenInput())

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

        request = kwargs.get('request', None)
        self.fields['fingerprint'].initial = get_random_fingerprint(request)

    def login(self, request, redirect_url=None):
        res = super(LoginForm, self).login(request, redirect_url)
        # check because of allauth author "misunderstanding" if user is trying to login with unconfirmed email:
        # https://github.com/pennersr/django-allauth/issues/254
        if allauth_app_settings.EMAIL_VERIFICATION == allauth_app_settings.EmailVerificationMethod.MANDATORY:
            login = self.cleaned_data['login']
            adapter = get_adapter(request)
            if self._is_login_email(login):
                emailaddress = EmailAddress.objects.filter(user=self.user,
                                                           email=login,
                                                           verified=False).first()
                if emailaddress is not None:
                    emailaddress.send_confirmation(request, signup=False)
                    res = adapter.respond_email_verification_sent(
                        request, self.user)

        return res


class BaseSignupForm(allauth_SignupForm):
    fingerprint = CharField(label='fingerprint', max_length=255, required=False, widget=HiddenInput())

    referer = CharField(label='referer', max_length=255, required=False, widget=HiddenInput(),
                        initial=app_settings.APP_URL)

    groups = CharField(label='groups', required=False)

    field_order = SIGNUP_FORM_FIELDS

    def __init__(self, *args, **kwargs):
        super(BaseSignupForm, self).__init__(*args, **kwargs)

        if 'username' not in app_settings.USER_FIELDS:
            self.fields.pop('username')
        if 'email' not in app_settings.USER_FIELDS:
            self.fields.pop('email')

        request = kwargs.get('request', None)
        self.fields['fingerprint'].initial = get_random_fingerprint(request)

    def get_form_kwargs(self):
        """Return the keyword arguments for instantiating the form."""
        kwargs = super(BaseSignupForm, self)
        return kwargs

    def save(self, request):
        new_user = super(BaseSignupForm, self).save(request)

        referer = self.cleaned_data["referer"]
        groups = self.cleaned_data.get("groups", '')

        try:
            if new_user is not None:
                # service subscription by "referer" field
                if referer not in (app_settings.APP_URL, '', None):
                    logger.info('Subscripting new user to service with url "{}"'.format(referer))

                    service = Service.objects.filter(service_url=referer).first()
                    if service is not None:
                        _subscription, _created = service.subscribe(new_user.get_sso_app_profile())

                # subscribing user to groups
                if len(groups):
                    group_names = groups.split(',')
                    logger.info('Subscripting new user to groups "{}"'.format(group_names))
                    for g in group_names:
                        group = Group.objects.filter(name=g).first()
                        if group is not None:
                            new_user.sso_app_profile.groups.add(group)


        # delete creating user model if any exception occurred
        except Exception as e:
            logger.exception('Error subscribing new user "{}"'.format(e))

            if new_user is not None:
                new_user.delete()

            raise

        return new_user


# custom signup form
if app_settings.BACKEND_SIGNUP_MUST_FILL_PROFILE:
    class SignupForm(BaseSignupForm):
        first_name = CharField(required='first_name' in app_settings.REQUIRED_PROFILE_FIELDS)
        last_name = CharField(required='last_name' in app_settings.REQUIRED_PROFILE_FIELDS)
        description = CharField(required='description' in app_settings.REQUIRED_PROFILE_FIELDS)
        picture = CharField(required='picture' in app_settings.REQUIRED_PROFILE_FIELDS)
        birthdate = DateField(required='birthdate' in app_settings.REQUIRED_PROFILE_FIELDS)
        latitude = FloatField(required='latitude' in app_settings.REQUIRED_PROFILE_FIELDS)
        longitude = FloatField(required='longitude' in app_settings.REQUIRED_PROFILE_FIELDS)
        country = CharField(required='country' in app_settings.REQUIRED_PROFILE_FIELDS)
        address = CharField(required='address' in app_settings.REQUIRED_PROFILE_FIELDS)
        # business_address = CharField(required='business_address' in app_settings.REQUIRED_PROFILE_FIELDS)
        language = CharField(required='language' in app_settings.REQUIRED_PROFILE_FIELDS)
        alias = CharField(required='alias' in app_settings.REQUIRED_PROFILE_FIELDS)

else:
    class SignupForm(BaseSignupForm):
        pass
