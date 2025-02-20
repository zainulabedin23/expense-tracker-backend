from rest_framework import serializers
from .models import Group, GroupMember
from django.contrib.auth import get_user_model

User = get_user_model()

class GroupMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMember
        fields = '__all__'

class GroupSerializer(serializers.ModelSerializer):
    members = GroupMemberSerializer(many=True, read_only=True)  # Nested members list

    class Meta:
        model = Group
        fields = ['id', 'name', 'created_by', 'created_at', 'members']

class GroupCreateSerializer(serializers.ModelSerializer):
    groupmemberName = serializers.ListField(write_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'created_by', 'groupmemberName']

    def create(self, validated_data):
        groupmember_data = validated_data.pop('groupmemberName', [])
        group = Group.objects.create(**validated_data)  # Create group

        # Add the creator to group members
        GroupMember.objects.create(group=group, user=group.created_by)

        # Add other members to the group
        for member in groupmember_data:
            user_id = member.get("userId")
            try:
                user_instance = User.objects.get(id=user_id)
                GroupMember.objects.create(group=group, user=user_instance)
            except User.DoesNotExist:
                raise serializers.ValidationError(f"User with ID {user_id} does not exist.")

        return group
