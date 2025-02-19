from django.urls import path
from .views import (
    GroupListCreateView, GroupDetailView,
    GroupMemberListCreateView, GroupMemberDetailView,UserGroupView
)

urlpatterns = [
    path('groups/', GroupListCreateView.as_view(), name='group-list-create'),  # ✅ List all groups or create a new group
    path('groups/<uuid:pk>/', GroupDetailView.as_view(), name='group-detail'),  # ✅ Retrieve, Update, or Delete a single group
    path('group-members/', GroupMemberListCreateView.as_view(), name='group-member-list-create'),  # ✅ List or Add Members to a Group
    path('group-members/<uuid:pk>/', GroupMemberDetailView.as_view(), name='group-member-detail'),  # ✅ Retrieve, Update, or Remove a Group Member
    path('user-groups/<uuid:user_id>/',UserGroupView.as_view(),name='user-groups')  # ✅ List all groups where the current user is a member
]
