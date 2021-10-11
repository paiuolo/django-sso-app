from django.db import models

from ...models import DeactivableModel, CreatedAtModel, MetaFieldModel, UpdatableModel


class EventListenerBaseModel(DeactivableModel, CreatedAtModel, UpdatableModel, MetaFieldModel):
    """
    EventListenerBaseModel

    """
    class Meta:
        abstract = True

    event_type = models.CharField(max_length=255, default='request_for_credentials')


class RequestForCredentialsEventListener(EventListenerBaseModel):
    """
    RequestForCredentialsEventListener

    """
    class Meta:
        app_label = 'django_sso_app'

    user_fields = ('username', 'email', 'password', 'is_active')
    profile_fields = ('sso_id', 'sso_rev', 'external_id', 'ssn', 'phone',
                      'first_name', 'last_name', 'alias', 'description', 'picture', 'birthdate', 'country_of_birth',
                      'latitude', 'longitude', 'country', 'address', 'language', 'gender', 'company_name',
                      'expiration_date')

    confirm_email = models.BooleanField(default=False)
    default_password = models.CharField(max_length=255, null=True, blank=True, default=None)

    # user
    is_active_field = models.CharField(max_length=255, default='is_active')

    username_field = models.CharField(max_length=255, default='username')
    email_field = models.CharField(max_length=255, default='email')
    password_field = models.CharField(max_length=255, default='password')

    # profile
    group_field = models.CharField(max_length=255, default='group')

    sso_id_field = models.CharField(max_length=255, default='sso_id')
    sso_rev_field = models.CharField(max_length=255, default='sso_rev')

    external_id_field = models.CharField(max_length=255, default='external_id')
    ssn_field = models.CharField(max_length=255, default='ssn')
    phone_field = models.CharField(max_length=255, default='phone')
    first_name_field = models.CharField(max_length=255, default='first_name')
    last_name_field = models.CharField(max_length=255, default='last_name')
    alias_field = models.CharField(max_length=255, default='alias')
    description_field = models.CharField(max_length=255, default='description')
    picture_field = models.CharField(max_length=255, default='picture')
    birthdate_field = models.CharField(max_length=255, default='birthdate')
    country_of_birth_field = models.CharField(max_length=255, default='country_of_birth')
    latitude_field = models.CharField(max_length=255, default='position.lat')
    longitude_field = models.CharField(max_length=255, default='position.lon')
    country_field = models.CharField(max_length=255, default='country')
    address_field = models.CharField(max_length=255, default='address')
    language_field = models.CharField(max_length=255, default='language')
    gender_field = models.CharField(max_length=255, default='gender')
    company_name_field = models.CharField(max_length=255, default='company_name')
    expiration_date_field = models.CharField(max_length=255, default='expiration_date')

    # device
    device_fingerprint_field = models.CharField(max_length=255, default='device_fingerprint')

    # service
    service_url_field = models.CharField(max_length=255, default='service_url')

    def __str__(self):
        return '{}:{}'.format(self.event_type, self.is_active)
