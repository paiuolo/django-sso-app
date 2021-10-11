from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from .views import SignupView, LoginView, LogoutView, EmailView, PasswordResetView, PasswordResetFromKeyView, \
                   PasswordChangeView, PasswordSetView


allauth_api_urlpatterns = [
    # allauth
    url(r"^api/v1/auth/signup/$", SignupView.as_view(), name="rest_signup"),
    url(r"^api/v1/auth/login/$", LoginView.as_view(), name="rest_login"),
    url(r"^api/v1/auth/logout/$", LogoutView.as_view(), name="rest_logout"),

    # E-mail
    url(r"^api/v1/auth/email/$", login_required(EmailView.as_view()), name="rest_email"),

    # Password
    url(r"^api/v1/auth/password/reset/$", PasswordResetView.as_view(), name="rest_password_reset"),
    url(r"^api/v1/auth/password/reset/key/$", PasswordResetFromKeyView.as_view(),
        name="rest_reset_password_from_key"),

    url(r"^api/v1/auth/password/change/$", PasswordChangeView.as_view(),
        name="rest_password_change"),

    url(r"^api/v1/auth/password/set/$", PasswordSetView.as_view(),
        name="rest_password_set"),
]
