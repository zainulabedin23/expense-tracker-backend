import django_filters
from .models import Group, GroupMember

class GroupFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Group
        fields = ['name', 'created_by']

class GroupMemberFilter(django_filters.FilterSet):
    group = django_filters.UUIDFilter()
    user = django_filters.UUIDFilter()

    class Meta:
        model = GroupMember
        fields = ['group', 'user']
