from django.urls import reverse

from rest_framework import serializers

from ...serializers import AbsoluteUrlSerializer, PartialObjectSerializer
from .models import Group, Grouping


class GroupSerializer(AbsoluteUrlSerializer):
    class Meta:
        model = Group
        read_only_fields = ('url', 'id', 'name')
        fields = read_only_fields


class GroupingListSerializer(AbsoluteUrlSerializer, PartialObjectSerializer):
    class Meta:
        model = Grouping
        read_only_fields = ('url', 'id', 'name', 'type', '_partial')
        fields = read_only_fields


class GroupingSerializer(AbsoluteUrlSerializer):
    group = serializers.SerializerMethodField(method_name='get_group_url')
    tree = serializers.SerializerMethodField(method_name='get_grouping_tree')

    class Meta:
        model = Grouping
        read_only_fields = ('url', 'id', 'name', 'type', 'group', 'description', 'tree')
        fields = read_only_fields

    def get_group_url(self, obj):
        request = self.context['request']
        _rel_rest_url = reverse("django_sso_app_group:rest-detail", args=[obj.name])

        return request.build_absolute_uri(_rel_rest_url)

    def get_grouping_tree(self, obj):
        def get_tree(n):
            node = {
                'node': {
                    'name': n.name,
                    'group': self.get_group_url(n),
                    'type': n.type,
                    'description': n.description,
                },
                'children': []
            }
            for c in n.get_children():
                node['children'].append(get_tree(c))

            return node

        return get_tree(obj)
