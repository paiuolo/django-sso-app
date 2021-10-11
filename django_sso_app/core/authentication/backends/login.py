from allauth.account.auth_backends import AuthenticationBackend as allauth_AuthenticationBackend

from ...utils import check_user_can_login
from ...permissions import is_authenticated

class DjangoSsoAppLoginAuthenticationBackend(allauth_AuthenticationBackend):
    def authenticate(self, request, **credentials):
        user = super(DjangoSsoAppLoginAuthenticationBackend, self).authenticate(request, **credentials)

        if is_authenticated(request.user):
            check_user_can_login(request.user,
                                 skip_profile_completion_checks=True, skip_service_subscription_checks=True)

        return user
