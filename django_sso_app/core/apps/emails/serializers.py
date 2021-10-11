from ...serializers import AbsoluteUrlSerializer
from .models import EmailAddress


class EmailSerializer(AbsoluteUrlSerializer):
    class Meta:
        model = EmailAddress
        read_only_fields = ('email', 'verified', 'primary')
        fields = read_only_fields
