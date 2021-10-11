import logging
import os

from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import SuspiciousOperation

from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from allauth.account.views import INTERNAL_RESET_URL_KEY, INTERNAL_RESET_SESSION_KEY
from allauth.account.forms import UserTokenForm
from allauth.utils import get_request_param
from allauth.account.adapter import get_adapter

from ..apps.emails.models import EmailAddress
from ..apps.users.serializers import SuccessfullLoginResponseSerializer, SuccessfullLogoutResponseSerializer
from ..apps.passepartout.utils import get_passepartout_login_redirect_url
from ..apps.emails.serializers import EmailSerializer
from ..permissions import is_authenticated
from ..utils import set_session_key, get_session_key, get_random_fingerprint
from .. import views as django_sso_app_views
from .. import app_settings

from .serializers import LoginSerializer, SignupSerializer, PasswordResetSerializer, PasswordResetFromKeySerializer, \
                         PasswordChangeSerializer, AddEmailSerializer, PasswordSetSerializer

sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters('password', 'password1', 'password2'))

logger = logging.getLogger('django_sso_app')

CURRENT_DIR = os.getcwd()
SUCCESS_STATUS_CODES = (status.HTTP_200_OK, status.HTTP_201_CREATED, status.HTTP_302_FOUND)
EMAIL_NOT_VERIFIED_MESSAGE = get_adapter().error_messages['email_not_verified']


class DjangoSsoAppApiViewMixin(APIView):
    # Form wrapper mixin
    http_method_names = ['get', 'post', 'head', 'options']

    __dssoa__is_api_view = True

    def __init__(self, *args, **kwargs):
        # object props
        self._initial = {}

        self.response_errors = 'Server error.'
        self.response_redirects_to_email_confirmation = False
        self.response_error_status = status.HTTP_500_INTERNAL_SERVER_ERROR

        super(DjangoSsoAppApiViewMixin, self).__init__(*args, **kwargs)

    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        return self._initial.copy()

    def get_request_fingerprint(self, request):
        return request.data.get('fingerprint', get_random_fingerprint(request))

    def get_error_response(self):
        return Response(self.response_errors, status=self.response_error_status)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(DjangoSsoAppApiViewMixin, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super(DjangoSsoAppApiViewMixin, self).form_valid(form)
        status_code = response.status_code

        if status_code not in SUCCESS_STATUS_CODES:
            raise Exception('Wrong status code "{}"'.format(status_code))

        location = response.get('location', None)
        if location == reverse('account_email_verification_sent'):
            self.response_redirects_to_email_confirmation = True

        return response

    def form_invalid(self, form):
        form_errors = dict(form.errors.items())

        if '__all__' in form_errors.keys():
            if len(form_errors['__all__']) == 1:
                parsed_errors = form_errors['__all__'][0]
            else:
                parsed_errors = form_errors['__all__']
        else:
            parsed_errors = form_errors

        self.response_error_status = status.HTTP_400_BAD_REQUEST
        self.response_errors = parsed_errors

        logger.debug('API Form errors "{}" -> "{}"'.format(form_errors, parsed_errors))

        raise serializers.ValidationError(parsed_errors)


# allauth views

class LoginView(DjangoSsoAppApiViewMixin, django_sso_app_views.LoginView):
    """
    Login
    """
    permission_classes = (AllowAny, )
    serializer_class = LoginSerializer
    http_method_names = ['post', 'head', 'options']
    email_not_verified_errors = EMAIL_NOT_VERIFIED_MESSAGE

    def get_form_kwargs(self, **kwargs):
        kwargs = super(LoginView, self).get_form_kwargs(**kwargs)

        kwargs['data'] ={
            'login': self.request.data.get('login', None),
            'password': self.request.data.get('password', None),
            'fingerprint': self.request.data.get('fingerprint', get_random_fingerprint(self.request)),
        }

        return kwargs

    def get_success_response(self):
        request = self.request
        data = {
            'user': request.user,
            'token': get_session_key(request, '__dssoa__jwt_token'),
            'redirect_url': get_passepartout_login_redirect_url(request),
        }
        serializer = SuccessfullLoginResponseSerializer(instance=data,
                                                        context={'request': self.request})

        response = Response(serializer.data, status=status.HTTP_200_OK)

        return response

    def post(self, request, *args, **kwargs):
        logger.info('API logging in')

        if is_authenticated(request.user):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            set_session_key(request, '__dssoa__device__fingerprint', self.get_request_fingerprint(request))

            _response = super(LoginView, self).post(request, *args, **kwargs)
            _status_code = _response.status_code

            # check user must confirm email
            if self.response_redirects_to_email_confirmation:
                self.response_error_status = status.HTTP_400_BAD_REQUEST
                self.response_errors = self.email_not_verified_errors

                raise Exception('Email not verified')

        except Exception as e:
            logger.exception('Error: {}'.format(e))
            return self.get_error_response()

        else:
            if is_authenticated(request.user):
                response = self.get_success_response()
            else:
                logger.info('user "{}" is not logged in'.format(request.user))

                # check user has unsubscribed
                user_unsubscribed_at = get_session_key(request, '__dssoa__user_is_unsubscribed', None)
                if user_unsubscribed_at is not None:
                    self.response_error_status = status.HTTP_400_BAD_REQUEST
                    self.response_errors = 'Unsubscribed at "{}"'.format(user_unsubscribed_at)

                # check user must confirm email
                if _response.get('location', None) == reverse('account_email_verification_sent'):
                    self.response_error_status = status.HTTP_400_BAD_REQUEST
                    self.response_errors = self.email_not_verified_errors

                return self.get_error_response()

            return self.get_response_with_cookie(request, response)


class LogoutView(DjangoSsoAppApiViewMixin, django_sso_app_views.LogoutView):
    """
    Logout
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.Serializer
    http_method_names = ['post', 'head', 'options']

    def get_success_response(self):
        request = self.request
        redirect_url = get_request_param(request, 'next')
        data = {
            'redirect_url': redirect_url
        }
        serializer = SuccessfullLogoutResponseSerializer(instance=data,
                                                         context={'request': self.request})

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        logger.info('API Logging out')

        if request.user and request.user.is_anonymous:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            _response = super(LogoutView, self).post(request, *args, **kwargs)
            _status_code = _response.status_code

            if _status_code not in SUCCESS_STATUS_CODES:
                logger.info('LogoutView status_code error ({})'.format(_status_code))

        except:
            return self.get_error_response()

        else:
            return self.get_response_with_invalidated_cookie(self.get_success_response())


class SignupView(DjangoSsoAppApiViewMixin, django_sso_app_views.SignupView):
    """
    Signup
    """
    permission_classes = (AllowAny, )
    serializer_class = SignupSerializer
    http_method_names = ['head', 'post', 'options']
    signup_form_fields = app_settings.USER_FIELDS + ('password1', 'password2',
                                                     'fingerprint',
                                                     'referer',
                                                     'groups')

    def get_form_kwargs(self, **kwargs):
        kwargs = super(SignupView, self).get_form_kwargs(**kwargs)

        data = {}
        for field in self.signup_form_fields:
            val = self.request.data.get(field, None)

            if field == 'groups':
                if val is not None and len(val):
                    val = ','.join(val)

            data[field] = val

        if app_settings.BACKEND_SIGNUP_MUST_FILL_PROFILE:
            for f in app_settings.PROFILE_FIELDS:
                data[f] = self.request.data.get(f, None)

        kwargs['data'] = data

        return kwargs

    def post(self, request, *args, **kwargs):
        logger.info('API Signing up')

        if is_authenticated(request.user):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            _response = super(SignupView, self).post(request, *args, **kwargs)

        except:
            return self.get_error_response()

        else:
            return Response(_('We have sent an e-mail to you for verification. Follow the link provided to finalize the signup process. Please contact us if you do not receive it within a few minutes.'), status=status.HTTP_200_OK)


class EmailView(DjangoSsoAppApiViewMixin, django_sso_app_views.EmailView):
    """
    Manage user email addresses
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = AddEmailSerializer
    http_method_names = ['get', 'post', 'head', 'options']

    def get_form_kwargs(self, **kwargs):
        kwargs = super(EmailView, self).get_form_kwargs(**kwargs)

        kwargs['data'] = {
            'email': self.request.data.get('email', None)
        }

        return kwargs

    def get(self, request, *args, **kwargs):
        logger.info('API Getting email')

        try:
            _response = super(EmailView, self).get(request, *args, **kwargs)

        except:
            return self.get_error_response()

        else:
            email_addresseses = EmailAddress.objects.filter(user=request.user)

            serializer = EmailSerializer(email_addresseses, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        logger.info('API adding new email')

        # set action_add as default
        request._request.POST = request._request.POST.copy()
        request._request.POST["action_add"] = ''

        try:
            _response = super(EmailView, self).post(request._request, *args, **kwargs)

        except:
            return self.get_error_response()

        else:
            return Response(_('We have sent an e-mail to you for verification. Please click on the link inside this e-mail. Please contact us if you do not receive it within a few minutes.'),
                            status=status.HTTP_200_OK)


class PasswordResetView(DjangoSsoAppApiViewMixin, django_sso_app_views.PasswordResetView):
    """
    Reset user password
    """
    permission_classes = (AllowAny, )
    serializer_class = PasswordResetSerializer
    http_method_names = ['head', 'post', 'options']

    def get_form_kwargs(self, **kwargs):
        kwargs = super(PasswordResetView, self).get_form_kwargs(**kwargs)

        kwargs['data'] = {
            'email': self.request.data.get('email', None)
        }

        return kwargs

    def post(self, request, *args, **kwargs):
        logger.info('API Asking for password reset')
        try:
            _response = super(PasswordResetView, self).post(request, *args, **kwargs)

        except:
            return self.get_error_response()

        else:
            return Response(_('We have sent you an e-mail. Please contact us if you do not receive it within a few minutes.'),
                            status=status.HTTP_200_OK)


class PasswordResetFromKeyView(DjangoSsoAppApiViewMixin, django_sso_app_views.PasswordResetFromKeyView):
    """
    Confirm user password reset
    """
    permission_classes = (AllowAny, )
    serializer_class = PasswordResetFromKeySerializer
    http_method_names = ['head', 'post', 'options']

    def get_form_kwargs(self, **kwargs):
        self.key = self.request.data.get('key')
        uidb36 = self.request.data.get('uidb36')

        token_form = UserTokenForm(
            data={'uidb36': uidb36, 'key': self.key})

        if token_form.is_valid():
            self.reset_user = token_form.reset_user

        else:
            logger.error('invalid password reset key')

            self.response_error_status = status.HTTP_400_BAD_REQUEST
            self.response_errors = _('The password reset link was invalid, possibly because it has already been used.  Please request a <a href="{}">new password reset</a>.'.format(reverse('account_reset_password')))

            raise SuspiciousOperation('Invalid password reset tokens')

        kwargs = super(PasswordResetFromKeyView, self).get_form_kwargs(**kwargs)

        kwargs['data'] = {
            'password1': self.request.data.get('password1', None),
            'password2': self.request.data.get('password2', None)
        }

        return kwargs

    def post(self, request, **kwargs):
        logger.info('Resetting password form key')
        try:
            key = self.request.data.get('key')
            uidb36 = self.request.data.get('uidb36')

            set_session_key(request, INTERNAL_RESET_SESSION_KEY, key)

            _response = super(PasswordResetFromKeyView, self).post(request, uidb36, INTERNAL_RESET_URL_KEY, **kwargs)

        except:
            return self.get_error_response()

        else:
            return Response(_('Your password is now changed.'), status=status.HTTP_200_OK)


class PasswordChangeView(DjangoSsoAppApiViewMixin, django_sso_app_views.PasswordChangeView):
    """
    Change user password
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = PasswordChangeSerializer
    http_method_names = ['head', 'post', 'options']

    def get_form_kwargs(self, **kwargs):
        kwargs = super(PasswordChangeView, self).get_form_kwargs(**kwargs)

        kwargs['data'] = {
            'oldpassword': self.request.data.get('oldpassword', None),
            'password1': self.request.data.get('password1', None),
            'password2': self.request.data.get('password2', None)
        }

        return kwargs

    def post(self, request, *args, **kwargs):
        logger.info('API Asking for password change')

        try:
            _response = super(PasswordChangeView, self).post(request, *args, **kwargs)

        except:
            return self.get_error_response()

        else:
            return Response(_('Password updated, <a href=\'/login/\'>LOGIN</a> with new credentials.'),
                            status=status.HTTP_200_OK)


class PasswordSetView(DjangoSsoAppApiViewMixin, django_sso_app_views.PasswordSetView):
    """
    Set user password
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = PasswordSetSerializer
    http_method_names = ['head', 'post', 'options']

    def get_form_kwargs(self, **kwargs):
        kwargs = super(PasswordSetView, self).get_form_kwargs(**kwargs)

        kwargs['data'] = {
            'password1': self.request.data.get('password1', None),
            'password2': self.request.data.get('password2', None)
        }

        return kwargs

    def post(self, request, *args, **kwargs):
        logger.info('API Asking for password set')

        if self.request.user.has_usable_password():
            return Response(_('Password already set.'), status=status.HTTP_400_BAD_REQUEST)

        try:
            _response = super(PasswordSetView, self).post(request, *args, **kwargs)

        except:
            return self.get_error_response()

        else:
            response = Response(_('Password successfully set.'),
                            status=status.HTTP_200_OK)

            self.update_response_jwt(request, response)

            return response
