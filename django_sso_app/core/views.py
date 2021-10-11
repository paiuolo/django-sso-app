import logging
import os

# from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import logout as django_logout

from rest_framework import status

from allauth.account import views as allauth_account_views
from allauth.account.adapter import get_adapter
from allauth.socialaccount import views as allauth_socialaccount_views

from .apps.devices.utils import renew_response_jwt
from .permissions import is_django_staff, is_authenticated, is_staff
from .tokens.utils import get_request_jwt
from .utils import set_cookie, invalidate_cookie, set_session_key, get_session_key, get_random_fingerprint
from .mixins import WebpackBuiltTemplateViewMixin
from . import app_settings

logger = logging.getLogger('django_sso_app')

CURRENT_DIR = os.getcwd()


class DjangoSsoAppBaseViewMixin:
    def update_response_jwt(self, user, response):
        """
        Updated response JWT (if in request)
        """
        if self.request is None:
            raise KeyError('no request object')

        requesting_user = self.request.user

        if not is_django_staff(requesting_user):
            logger.info('Updating response jwt for "{}"'.format(user))
            received_jwt = get_request_jwt(self.request)

            if received_jwt is not None:
                is_same_user = requesting_user == user

                if is_same_user:
                    logger.info('From browser as same user "{}"'.format(user))
                    renew_response_jwt(received_jwt, user, self.request, response)

                elif not is_same_user and is_staff(requesting_user):
                    # returns user jwt to staff user  #Q!
                    logger.info('From browser as staff user "{}"'.format(requesting_user))
                    renew_response_jwt(received_jwt, user, self.request, response)

                else:
                    _msg = 'User "{}" can not update response JWT for "{}"'.format(requesting_user, user)
                    logger.warning(_msg)

                    raise SuspiciousOperation(_msg)


class DjangoSsoAppViewMixin(DjangoSsoAppBaseViewMixin):
    def __init__(self, *args, **kwargs):
        super(DjangoSsoAppViewMixin, self).__init__(*args, **kwargs)

        if not hasattr(self, 'object'):
            setattr(self, 'object', None)

    @staticmethod
    def get_request_fingerprint(request):
        return request.POST.get('fingerprint', get_random_fingerprint(request))

    @staticmethod
    def get_response_with_cookie(request, response):
        if is_authenticated(request.user):
            if not is_django_staff(request.user):
                token = get_session_key(request, '__dssoa__jwt_token')
                set_cookie(response, app_settings.JWT_COOKIE_NAME, token)

        return response

    @staticmethod
    def get_response_with_invalidated_cookie(response):
        invalidate_cookie(response, app_settings.JWT_COOKIE_NAME)

        return response


# allauth views

class LoginView(allauth_account_views.LoginView, DjangoSsoAppViewMixin, WebpackBuiltTemplateViewMixin):

    def get(self, request, *args, **kwargs):
        logger.info('Getting login')

        try:
            return super(LoginView, self).get(request, *args, **kwargs)

        except:
            logger.exception('Error getting login')
            raise

    def post(self, request, *args, **kwargs):
        logger.info('Logging in')

        try:
            set_session_key(request, '__dssoa__device__fingerprint', self.get_request_fingerprint(request))
            response = super(LoginView, self).post(request, *args, **kwargs)
            location = response.get('location', None)
            if location == reverse('account_email_verification_sent'):
                # disable login on signup
                logger.info('User "must confirm email"'.format(request.user))

                adapter = get_adapter(self.request)
                adapter.logout(request)

        except:
            logger.exception('Error logging in')
            raise

        else:
            if is_authenticated(request.user):
                logger.info('login success')
                response = self.get_response_with_cookie(request, response)

            return response


class LogoutView(allauth_account_views.LogoutView, DjangoSsoAppViewMixin, WebpackBuiltTemplateViewMixin):
    def get(self, request, *args, **kwargs):
        logger.info('Getting logout')

        if request.user and request.user.is_anonymous:
            return redirect(reverse('account_login'))

        try:
            return super(LogoutView, self).get(request, *args, **kwargs)

        except:
            logger.exception('Error getting logout')
            raise

    def post(self, request, *args, **kwargs):
        logger.info('Logging out')

        if request.user and request.user.is_anonymous:
            return redirect(reverse('account_login'))

        try:
            response = super(LogoutView, self).post(request, *args, **kwargs)

        except:
            logger.exception('Error logging out')
            raise

        else:
            return self.get_response_with_invalidated_cookie(response)


class SignupView(allauth_account_views.SignupView, DjangoSsoAppViewMixin, WebpackBuiltTemplateViewMixin):
    def get(self, request,  *args, **kwargs):
        logger.info('Getting signup')

        if is_authenticated(request.user):
            return redirect(reverse('account_login'))

        try:
            return super(SignupView, self).get(request, *args, **kwargs)

        except:
            logger.exception('Error getting signup')
            raise

    def post(self, request, *args, **kwargs):
        logger.info('Signing up')

        if is_authenticated(request.user):
            return redirect(reverse('account_login'))

        try:
            response = super(SignupView, self).post(request, *args, **kwargs)

        except:
            logger.exception('Error signin up')
            raise

        else:
            # log signup failed
            if response.status_code not in (200, 302):
                if hasattr(response, 'render'):
                    response.render()
                logger.warning('User failed to register: "{}"'.format(response.content))

            if is_authenticated(request.user):
                logger.debug('signup login disabled')
                django_logout(request)

        return response


class ConfirmEmailView(allauth_account_views.ConfirmEmailView, DjangoSsoAppViewMixin):
    def get(self, request, *args, **kwargs):
        logger.info('Getting confirm email')

        try:
            response = super(ConfirmEmailView, self).get(request, *args, **kwargs)

        except:
            logger.exception('Error get confirm email')
            raise

        else:
            if is_authenticated(request.user):
                response = self.get_response_with_cookie(request, response)

            return response

    def post(self, request, *args, **kwargs):
        logger.info('Confirming email')

        try:
            response = super(ConfirmEmailView, self).post(request, *args, **kwargs)

        except:
            logger.exception('Error confirming email')
            raise

        else:
            if is_authenticated(request.user):
                response = self.get_response_with_cookie(request, response)

            return response


class EmailView(allauth_account_views.EmailView):
    def get(self, *args, **kwargs):
        logger.info('Getting email')

        try:
            return super(EmailView, self).get(*args, **kwargs)

        except:
            logger.exception('Error getting email')
            raise

    def post(self, request, *args, **kwargs):
        logger.info('Posting email')

        try:
            response = super(EmailView, self).post(request, *args, **kwargs)

        except:
            logger.exception('Error email')
            raise

        return response


class PasswordChangeView(allauth_account_views.PasswordChangeView):
    def get(self, *args, **kwargs):
        logger.info('Getting password change')

        try:
            return super(PasswordChangeView, self).get(*args, **kwargs)

        except:
            logger.exception('Error getting password change')
            raise

    def post(self, *args, **kwargs):
        logger.info('Changing password')

        try:
            return super(PasswordChangeView, self).post(*args, **kwargs)

        except:
            logger.exception('Error changing password')
            raise


class PasswordSetView(allauth_account_views.PasswordSetView, DjangoSsoAppViewMixin):
    def get(self, *args, **kwargs):
        logger.info('Getting password set')

        try:
            return super(PasswordSetView, self).get(*args, **kwargs)

        except:
            logger.exception('Error getting password set')
            raise

    def post(self, request, *args, **kwargs):
        logger.info('Setting password')

        try:
            response = super(PasswordSetView, self).post(request, *args, **kwargs)

        except:
            logger.exception('Error setting password')
            raise

        else:
            self.update_response_jwt(request.user, response)

            return response


class PasswordResetView(allauth_account_views.PasswordResetView, DjangoSsoAppViewMixin, WebpackBuiltTemplateViewMixin):
    def get(self, *args, **kwargs):
        logger.info('Getting ask password reset')

        try:
            return super(PasswordResetView, self).get(*args, **kwargs)

        except:
            logger.exception('Error getting ask password reset')
            raise

    def post(self, *args, **kwargs):
        logger.info('Asking for password reset')

        try:
            return super(PasswordResetView, self).post(*args, **kwargs)

        except:
            logger.exception('Error while asking password reset')
            raise


class PasswordResetDoneView(allauth_account_views.PasswordResetDoneView):
    def get(self, request, *args, **kwargs):
        logger.info('Getting password reset done')

        try:
           return super(PasswordResetDoneView, self).get(request, *args, **kwargs)

        except:
            logger.exception('Error getting password reset done')
            raise


class PasswordResetFromKeyView(allauth_account_views.PasswordResetFromKeyView, DjangoSsoAppViewMixin, WebpackBuiltTemplateViewMixin):

    def dispatch(self, request, uidb36, key, **kwargs):
        _response = super(PasswordResetFromKeyView, self).dispatch(request, uidb36, key, **kwargs)
        _status_code = _response.status_code

        if app_settings.BACKEND_FRONTEND_APP_RESTONLY and _status_code == status.HTTP_302_FOUND:
            template_name = self.get_template_names()[0]
            logger.debug('Frontend is rest only, returning template "{}"'.format(template_name))
            template = loader.get_template(template_name)
            context = {}

            return HttpResponse(template.render(context, request))

        return _response

    def get(self, request, uidb36, key, **kwargs):
        logger.info('Getting password reset from key')

        try:
            return super(PasswordResetFromKeyView, self).get(request, uidb36, key, **kwargs)

        except:
            logger.exception('Error while getting password reset from key')
            raise

    def post(self, request, uidb36, key, **kwargs):
        logger.info('Resetting password form key')

        try:
            return super(PasswordResetFromKeyView, self).post(request, uidb36, key, **kwargs)

        except:
            logger.exception('Error while resetting password form key')
            raise


class PasswordResetFromKeyDoneView(allauth_account_views.PasswordResetFromKeyDoneView):
    def get(self, *args, **kwargs):
        logger.info('Getting password reset from key done')
        try:
            return super(PasswordResetFromKeyDoneView, self).get(*args,
                                                                 **kwargs)
        except:
            logger.exception('Error while getting password reset from key done')
            raise


class AccountInactiveView(allauth_account_views.AccountInactiveView):
    def get(self, *args, **kwargs):
        logger.info('Getting account inactive')

        try:
            return super(AccountInactiveView, self).get(*args, **kwargs)

        except:
            logger.exception('Error while getting account inactive')
            raise


class EmailVerificationSentView(allauth_account_views.EmailVerificationSentView, DjangoSsoAppViewMixin, WebpackBuiltTemplateViewMixin):
    def get(self, *args, **kwargs):
        logger.info('Getting email verification sent')

        try:
            return super(EmailVerificationSentView, self).get(*args, **kwargs)

        except:
            logger.exception('Error getting verification sent')
            raise


# allauth socialaccount views
class SocialSignupView(allauth_socialaccount_views.SignupView):
    pass


class SocialLoginCancelledView(allauth_socialaccount_views.LoginCancelledView):
    pass


class SocialLoginErrorView(allauth_socialaccount_views.LoginErrorView):
    pass


class SocialConnectionsView(allauth_socialaccount_views.ConnectionsView):
    pass
