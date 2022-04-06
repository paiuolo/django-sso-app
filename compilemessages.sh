#!/bin/bash

django-admin compilemessages -l de -l en -l es -l fr -l it --ignore '.tox/*' --ignore '.venv/*'
