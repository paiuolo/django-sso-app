#!/bin/bash

python manage.py makemessages -e txt -e html -e py --no-wrap --no-obsolete --no-default-ignore -a -v 2 -i "node_modules/*" -i "backend/templates/old/*"

python manage.py makemessages -d djangojs -e vue -e js --no-wrap --no-obsolete --no-default-ignore -a -v 2 -i "node_modules/*" -i "virtualenv/*"
