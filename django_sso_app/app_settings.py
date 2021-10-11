import sys
from .core import app_settings  # noqa


app_settings.__name__ = __name__
sys.modules[__name__] = app_settings
