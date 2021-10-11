from .core.settings.common import *


if DJANGO_SSO_APP_SHAPE in BACKEND_SHAPES:
    from .backend.settings import *
else:
    from .app.settings import *
