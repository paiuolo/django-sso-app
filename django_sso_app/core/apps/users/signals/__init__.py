import sys

from .... import app_settings


signals_enabled = True
for c in app_settings.SIGNALS_DISABLED_COMMANDS:
    if c in sys.argv:
        signals_enabled = False
        break

if signals_enabled:
    if app_settings.BACKEND_ENABLED:
        from .backend import *
    else:
        from .app import *
