from django.http import HttpResponseRedirect
from django.views import View

from ..core import app_settings


class AppLoginView(View):

    def get(self, request, *args, **kwargs):
        next = request.GET.get('next', '')
        return HttpResponseRedirect(app_settings.REMOTE_LOGIN_URL + next)


class AppSignupView(View):

    def get(self, request, *args, **kwargs):
        next = request.GET.get('next', '')
        return HttpResponseRedirect(app_settings.REMOTE_SIGNUP_URL + next)


class AppLogoutView(View):

    def get(self, request, *args, **kwargs):
        next = request.GET.get('next', '')
        return HttpResponseRedirect(app_settings.REMOTE_LOGOUT_URL + next)
