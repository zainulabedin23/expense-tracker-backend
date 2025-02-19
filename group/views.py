from rest_framework import generics, permissions
from .models import Group, GroupMember
from .serializers import GroupSerializer, GroupMemberSerializer

# ✅ List all groups or create a new group
class GroupListCreateView(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """
        When a user creates a group:
        1. Assign them as the 'created_by' user.
        2. Automatically add them to 'GroupMember' table.
        """
        group = serializer.save(created_by=self.request.user)  # Step 1: Save the group
        
        # Step 2: Add the creator to the GroupMember table
        GroupMember.objects.create(group=group, user=self.request.user)

# ✅ Retrieve, Update, or Delete a single group
class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

# ✅ List or Add Members to a Group
class GroupMemberListCreateView(generics.ListCreateAPIView):
    queryset = GroupMember.objects.all()
    serializer_class = GroupMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

# ✅ Retrieve, Update, or Remove a Group Member
class GroupMemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GroupMember.objects.all()
    serializer_class = GroupMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserGroupView(generics.ListAPIView):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return all groups where the given UUID user ID is a member."""
        user_id = self.kwargs.get("user_id")  # Extract UUID user ID from the URL
        return Group.objects.filter(members__user_id=user_id)
