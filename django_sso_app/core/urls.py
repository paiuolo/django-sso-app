from importlib import import_module

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.urls import include
from django.views.generic.base import RedirectView

from allauth import app_settings
from allauth.socialaccount import providers
# from allauth.socialaccount.providers.google.urls import urlpatterns as allauth_aocialaccount_google_urlpatterns

from .views import SignupView, LoginView, LogoutView, PasswordChangeView, PasswordSetView, \
                   AccountInactiveView, EmailView, EmailVerificationSentView, ConfirmEmailView, PasswordResetView, \
                   PasswordResetDoneView, PasswordResetFromKeyView, PasswordResetFromKeyDoneView, \
                   SocialSignupView, SocialLoginCancelledView, SocialLoginErrorView, SocialConnectionsView


allauth_i18n_urlpatterns = [
    url(r"^signup/$", SignupView.as_view(), name="account_signup"),
    url(r"^login/$", LoginView.as_view(), name="account_login"),
    url(r"^logout/$", LogoutView.as_view(), name="account_logout"),
]

allauth_urlpatterns = [
    # Password
    url(r"^password/change/$", login_required(PasswordChangeView.as_view()),
        name="account_change_password"),
    url(r"^password/set/$", login_required(PasswordSetView.as_view()), name="account_set_password"),

    # password reset
    url(r"^password/reset/$", PasswordResetView.as_view(),
        name="account_reset_password"),
    url(r"^password/reset/done/$", PasswordResetDoneView.as_view(),
        name="account_reset_password_done"),

    # SPA frontend required view
    url(r"^password/reset/key/$", RedirectView.as_view(url='/password/reset/', permanent=False),
        name="account_reset_password_key_redirect"),

    url(r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)/(?P<key>.+)/$",
        PasswordResetFromKeyView.as_view(),
        name="account_reset_password_from_key"),
    url(r"^password/reset/key/done/$", PasswordResetFromKeyDoneView.as_view(),
        name="account_reset_password_from_key_done"),

    # E-mail
    url(r"^email/$", login_required(EmailView.as_view()), name="account_email"),

    url(r"^confirm-email/$", EmailVerificationSentView.as_view(),
        name="account_email_verification_sent"),

    url(r"^inactive/$", AccountInactiveView.as_view(), name="account_inactive"),

    url(r"^confirm-email/(?P<key>[-:\w]+)/$", ConfirmEmailView.as_view(),
        name="account_confirm_email"),

    # completely overridden
    # url(r'', include('allauth.urls')),
]

if app_settings.SOCIALACCOUNT_ENABLED:
    allauth_socialaccount_urlpatterns = []

    allauth_socialaccount_urlpatterns += [
        url(r'^login/cancelled/$', SocialLoginCancelledView.as_view(),
            name='socialaccount_login_cancelled'),
        url(r'^login/error/$', SocialLoginErrorView.as_view(),
            name='socialaccount_login_error'),
        url(r'^signup/$', SocialSignupView.as_view(), name='socialaccount_signup'),
        url(r'^connections/$', SocialConnectionsView.as_view(), name='socialaccount_connections'),

    ]

    # taken from allauth.urls
    # Provider urlpatterns, as separate attribute (for reusability).
    provider_urlpatterns = []
    for provider in providers.registry.get_list():
        try:
            prov_mod = import_module(provider.get_package() + '.urls')
        except ImportError:
            continue
        prov_urlpatterns = getattr(prov_mod, 'urlpatterns', None)
        if prov_urlpatterns:
            allauth_socialaccount_urlpatterns += prov_urlpatterns

    allauth_urlpatterns += [
        url(r'^social/', include(allauth_socialaccount_urlpatterns)),
    ]

    # completely overridden
    # url(r'^social/', include('allauth.socialaccount.urls'))
