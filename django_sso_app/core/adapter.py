import logging
# import inspect
# import warnings

from django.db import transaction
from django.urls import reverse
from django.contrib.auth import authenticate
from django.utils.translation import activate as activate_translation

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from rest_framework.renderers import JSONRenderer

from allauth.account.adapter import DefaultAccountAdapter, app_settings as allauth_app_settings

from .apps.emails.utils import unconfirm_all_user_emails
from .apps.passepartout.utils import get_passepartout_login_redirect_url
from . import app_settings

logger = logging.getLogger('django_sso_app')


class AccountAdapter(DefaultAccountAdapter):
    def __init__(self, request=None):
        super(AccountAdapter, self).__init__(request)

        self.error_messages = DefaultAccountAdapter.error_messages
        self.error_messages['email_not_verified'] = _('We have sent an e-mail to you for verification. Follow the link provided to finalize the signup process. Please contact us if you do not receive it within a few minutes.')

    def populate_username(self, request, user):
        # new user has username == email
        user.username = user.email

    def is_ajax(self, request):
        is_ajax = request.path.startswith('/api') or \
                  super(AccountAdapter, self).is_ajax(request) or \
                  request.META.get('CONTENT_TYPE', None) == 'application/json'

        return is_ajax

    def ajax_response(self, request, response, redirect_to=None, form=None, data=None):
        # manually setting response renderer
        setattr(response, 'accepted_renderer', JSONRenderer())
        setattr(response, 'accepted_media_type', 'application/json')
        setattr(response, 'renderer_context', {})

        return super(AccountAdapter, self).ajax_response(request, response, redirect_to, form, data)

    def get_login_redirect_url(self, request):
        """
        Returns the default URL to redirect to after logging in.  Note
        that URLs passed explicitly (e.g. by passing along a `next`
        GET parameter) take precedence over the value returned here.
        """

        if request.path.startswith(reverse('account_signup')) or request.path.startswith(reverse('rest_signup')):
            logger.info('do not get redirect_url from signup')
            redirect_url = None
        else:
            redirect_url = get_passepartout_login_redirect_url(request)

            if redirect_url is None:
                redirect_url = super(AccountAdapter, self).get_login_redirect_url(request)

        return redirect_url

    def login(self, request, user):
        # HACK: This is not nice. The proper Django way is to use an
        # authentication backend
        logger.debug('Adapter login')

        super(AccountAdapter, self).login(request, user)

    def logout(self, request):
        # allauth logout
        super(AccountAdapter, self).logout(request)

    def confirm_email(self, request, email_address):
        """
        Marks the email address as confirmed on the db,
        deletes old user emails.
        """
        email_address.verified = True
        email_address.set_as_primary(conditional=False)
        email_address.save()

        # one email per user
        email_address.user.emailaddress_set.exclude(email=email_address).delete()

    def set_password(self, user, password):
        user.set_password(password)
        user.save()

    @transaction.atomic
    def save_user(self, request, user, form, commit=True):
        """
        Saves a new User instance using information provided in the
        signup form.
        """
        return super(AccountAdapter, self).save_user(request, user, form, commit)

    def render_mail(self, template_prefix, email, context):
        user = context.get('user')
        logger.info('render mail for "{}"'.format(user))
        user_language = user.sso_app_profile.language

        activate_translation(user_language)
        context.update({
            'EMAILS_DOMAIN': settings.COOKIE_DOMAIN,
            'EMAILS_SITE_NAME': settings.APP_DOMAIN
        })

        return super(AccountAdapter, self).render_mail(template_prefix, email, context)

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Constructs the email confirmation (activation) url.
        Note that if you have architected your system such that email
        confirmations are sent outside of the request context request
        can be None here.
        """
        _url = reverse(
            "account_confirm_email",
            args=[emailconfirmation.key])

        email_confirmation_url = '{}://{}{}'.format(app_settings.HTTP_PROTOCOL,
                                                    settings.APP_DOMAIN,
                                                    _url)

        return email_confirmation_url

    # pai

    def unconfirm_all_user_emails(self, user):
        return unconfirm_all_user_emails(user, self.request)

    def update_user_email(self, user, new_email):
        user.email = new_email  # set user model email

        setattr(user, '__dssoa__email_updated', True)

        user.save()

    def update_user_username(self, user, new_username):
        user.username = new_username  # set user model username

        setattr(user, '__dssoa__username_updated', True)

        user.save()
