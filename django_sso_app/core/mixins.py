from django.contrib.auth import get_user_model
from django.views.generic import TemplateView

from . import app_settings

User = get_user_model()


class WebpackBuiltTemplateViewMixin(TemplateView):
    """
    Uses built template view when DJANGO_SSO_APP_BACKEND_HAS_CUSTOM_FRONTEND_APP
    """

    def get_template_names(self):
        if app_settings.BACKEND_HAS_CUSTOM_FRONTEND_APP:
            original_template_path = getattr(self, 'template_name')
            relative_template_path = original_template_path

            return [relative_template_path]
        else:
            return [getattr(self, 'template_name')]

    def get_context_data(self, *args, **kwargs):
        context = super(WebpackBuiltTemplateViewMixin, self).get_context_data(*args, **kwargs)
        return context
