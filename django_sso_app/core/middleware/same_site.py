from django.utils.deprecation import MiddlewareMixin

from .. import app_settings


class SameSiteMiddleware(MiddlewareMixin):

    def process_response(self, request, response):

        if app_settings.SAME_SITE_COOKIE_NONE:
            if 'jwt' in response.cookies:
                response.cookies['jwt']['samesite'] = 'None'

        return response
