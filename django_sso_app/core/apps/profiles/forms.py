import logging

import base64
from io import BytesIO
from PIL import Image

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

from django_countries.fields import CountryField

from ... import app_settings
from .models import Profile

logger = logging.getLogger('django_sso_app')


class ProfileForm(forms.Form):
    # role = forms.ChoiceField(
    #     label=_('Role'),
    #     choices=app_settings.PROFILE_ROLE_CHOICES,
    #     initial=0)

    ssn = forms.CharField(
        label=_('Social Security Number'),
        widget=forms.TextInput(
            attrs={'type': 'text',
                   'placeholder': _('Social Security Number')}))

    phone = forms.CharField(
        label=_('Phone'),
        widget=forms.TextInput(
            attrs={'type': 'text',
                   'placeholder': _('Phone')}))

    first_name = forms.CharField(
        label=_('First name'),
        widget=forms.TextInput(
            attrs={'type': 'text',
                   'placeholder': _('First name')}))

    last_name = forms.CharField(
        label=_('Last name'),
        widget=forms.TextInput(
            attrs={'type': 'text',
                   'placeholder': _('Last name')}))

    description = forms.CharField(
        label=_('Description'),
        widget=forms.Textarea(
            attrs={'placeholder': _('Description'),
                   'rows': 2}))

    picture = forms.ImageField(
        label=_('Picture'),
        widget=forms.ClearableFileInput(attrs={'multiple': False})
    )

    birthdate = forms.DateField(
        label=_('Birthdate'),
        widget=forms.TextInput(
            attrs={'type': 'date',
                   'placeholder': _('Birthdate')}))
    """
    country_of_birth = forms.CharField(
        label=_('Country of birth'),
        widget=forms.TextInput(
            attrs={'type': 'text',
                   'placeholder': _('Country of birth')}))
    """
    country_of_birth = CountryField().formfield(label=_('Country of birth'))

    latitude = forms.FloatField(label=_('Latitude'))

    longitude = forms.FloatField(label=_('Longitude'))

    """
    country = forms.CharField(
        label=_('Country'),
        widget=forms.TextInput(
            attrs={'type': 'text',
                   'placeholder': _('Country')}))
    """
    country = CountryField().formfield(label=_('Country'))

    address = forms.CharField(
        label=_('Address'),
        widget=forms.Textarea(
            attrs={'placeholder': _('Address'),
                   'rows': 1}))

    language = forms.CharField(
        label=_('Language'),
        widget=forms.TextInput(
            attrs={'type': 'text',
                   'placeholder': _('Language')}))

    gender = forms.CharField(
        label=_('Gender'),
        widget=forms.TextInput(
            attrs={'type': 'text',
                   'placeholder': _('Gender')}))

    company_name = forms.CharField(
        label=_('Company name'),
        widget=forms.TextInput(
            attrs={'type': 'text',
                   'placeholder': _('Company name')}))

    def set_required_fields(self):
        for field in app_settings.PROFILE_FIELDS:
            if field in self.fields.keys():
                self.fields[field].required = field in app_settings.REQUIRED_PROFILE_FIELDS

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)

        self.set_required_fields()

    def clean_picture(self):
        picture_file = self.cleaned_data['picture']
        picture_file_type = type(picture_file)

        if picture_file_type not in (str, None) and picture_file_type in (InMemoryUploadedFile, TemporaryUploadedFile):
            picture_bin = picture_file.file.read()
            picture_image = Image.open(BytesIO(picture_bin))
            picture_format = picture_image.format

            if picture_format not in ('PNG', 'JPEG'):
                raise forms.ValidationError('Image must be either PNG or JPEG')

            picture_image.thumbnail((100, 100), Image.ANTIALIAS)

            image = BytesIO()
            picture_image.save(image, format=picture_format)

            return "data:image/{};base64,".format(picture_format.lower()) + base64.b64encode(image.getvalue()).decode(
                'utf-8')
        else:
            return None


class UserProfileForm(forms.ModelForm, ProfileForm):
    class Meta:
        model = Profile
        fields = app_settings.PROFILE_FIELDS
