from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from .models import Group, GroupMember
from .serializers import GroupSerializer, GroupMemberSerializer, GroupCreateSerializer
from .filters import GroupFilter, GroupMemberFilter
from .permissions import IsGroupOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated
# from rest_framework.permissions import IsAuthenticated

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = GroupFilter
    # is authenticated is not there in permissions
    permission_classes = [IsGroupOwnerOrReadOnly]

    def get_serializer_class(self):
        """Use a different serializer for group creation with members."""
        if self.action == 'create':
            return GroupCreateSerializer
        return GroupSerializer
    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def get_user_groups(self, request, user_id=None):
        """
        Fetch all groups where a user is a member, along with all group members.
        """
        # 🔹 Use 'members' instead of 'group_members'
        user_groups = Group.objects.filter(members__user_id=user_id).distinct()

        response_data = []
        for group in user_groups:
            members = GroupMember.objects.filter(group=group).select_related('user')
            member_list = [{"user_id": member.user.id, "username": member.user.username,"group_member_id":member.id} for member in members]

            response_data.append({
                "group_id": group.id,
                "owner": group.created_by_id,
                "group_name": group.name,
                "members": member_list
            })
            

        return Response(response_data)

class GroupMemberViewSet(viewsets.ModelViewSet):
    queryset = GroupMember.objects.all()
    serializer_class = GroupMemberSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = GroupMemberFilter
    permission_classes = [IsGroupOwnerOrReadOnly]
