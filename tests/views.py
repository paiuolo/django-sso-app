import datetime

from django.http import HttpResponse
from django.template import Template, Context


def home(request):
    now = datetime.datetime.now()
    template = '{% extends "base.html" %}{% block content %}Hello {{ request.user }}<br/>It is now ' + \
               now.isoformat() + '.{% endblock %}'

    t = Template(template)
    c = Context({"request": request})

    return HttpResponse(t.render(c))
