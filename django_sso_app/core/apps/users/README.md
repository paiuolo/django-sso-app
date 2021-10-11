# core.apps.users

> Proxy model for allauth/rest_auth/groups logic.

When a new user is created by allauth/rest_auth logics **django_sso_app.core.apps.profiles** is responsible to store
user personal data.

Groups model is also linked to enable extra authorization policies.

This model is responsible of getting accounting informations, as username, email or admin stuff..
Profile updates are implemented by profiles api.
 