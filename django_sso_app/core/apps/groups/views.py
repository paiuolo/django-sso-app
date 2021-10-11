from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.response import Response

from .serializers import GroupSerializer, GroupingSerializer, GroupingListSerializer
from .models import Group, Grouping


class GroupApiViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = GroupSerializer
    queryset = Group.objects.all()
    lookup_field = 'name'
    permission_classes = (permissions.IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        """
        List groups
        """
        return super(GroupApiViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Group detail
        """
        return super(GroupApiViewSet, self).retrieve(request, *args, **kwargs)


class GroupingApiViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Grouping.get_root_nodes()
    lookup_field = 'pk'
    permission_classes = (permissions.IsAuthenticated, )

    def get_serializer_class(self):
        if self.action == 'list':
            return GroupingListSerializer
        else:
            return GroupingSerializer

    def list(self, request, *args, **kwargs):
        """
        List groupings
        """
        return super(GroupingApiViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, pk=None, *args, **kwargs):
        """
        Grouping detail
        """

        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
