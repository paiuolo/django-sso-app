import os

from django.apps import apps
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.filesystem import Loader as BaseLoader


class Loader(BaseLoader):
    is_usable = True

    def get_template_sources(self, tpl):
        template_parts = tpl.split(":", 1)

        if len(template_parts) != 2:
            raise TemplateDoesNotExist(tpl)

        app_name, template_name = template_parts
        app = apps.get_app_config(app_name)
        template_dir = os.path.abspath(os.path.join(app.path, 'templates'))
        path = os.path.join(template_dir, template_name)

        yield Origin(
            name=path,
            template_name=tpl,
            loader=self,
        )
