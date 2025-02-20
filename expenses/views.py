from rest_framework import viewsets
from .models import Expense, ExpenseSplit
from .serializers import ExpenseSerializer, ExpenseSplitSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from group.models import Group
#class ExpenseViewSet(viewsets.ModelViewSet):
#    queryset = Expense.objects.all()
#    serializer_class = ExpenseSerializer

#   def perform_create(self, serializer):
#        expense = serializer.save()
#        # You can optionally create corresponding ExpenseSplits after the Expense is saved.
#       # Assuming you are passing this information in the request body
#       splits_data = self.request.data.get('splits', [])
#       for split in splits_data:
#           ExpenseSplit.objects.create(expense=expense, **split)
from django.contrib.auth import get_user_model
 
User = get_user_model()  # Get the User model dynamically
 
class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
 
    def perform_create(self, serializer):
        """
        Handles both personal and group expenses:
        - If the type is 'group', also create corresponding ExpenseSplit entries.
        """
        expense = serializer.save(owner=self.request.user)  # Save expense first
 
        # If expense type is 'group', create ExpenseSplit records
        if expense.type == 'group':
            splits = self.request.data.get("splits", [])
            for split in splits:
                user_id = split.get("user")  # Get user UUID
                amount = split.get("amount")
                status = split.get("status", "pending")
 
                # ✅ Fetch the actual User instance
                try:
                    user_instance = User.objects.get(id=user_id)
                    ExpenseSplit.objects.create(
                        expense=expense, user=user_instance, amount=amount, status=status
                    )
                except User.DoesNotExist:
                    raise serializers.ValidationError(f"User with ID {user_id} does not exist.")
                
    @action(detail=False, methods=['get'], url_path='group-expenses/(?P<group_id>[^/.]+)')
    def get_group_expenses(self, request, group_id=None):
        """
        Get all expenses for a given group along with split details.
        """
        # 1️⃣ Validate if the group exists
        group = get_object_or_404(Group, id=group_id)

        # 2️⃣ Fetch all expenses related to this group
        expenses = Expense.objects.filter(group=group.id)

        # 3️⃣ Fetch split expense details
        response_data = {
            "group_id": group.id,
            "expenses": []
        }

        for expense in expenses:
            splits = ExpenseSplit.objects.filter(expense_id=expense.id).select_related("user")

            split_details = [
                {
                    "user_id": split.user.id,
                    "username": split.user.username,  # Fetch username from User model
                    "amount": split.amount,
                    "status": split.status
                }
                for split in splits
            ]

            response_data["expenses"].append({
                "expense_id": expense.id,
                "amount": expense.amount,
                "category": expense.category,
                "description": expense.description,
                "payment_date": expense.payment_date,
                "splits": split_details
            })

        return Response(response_data)

class ExpenseSplitViewSet(viewsets.ModelViewSet):
    queryset = ExpenseSplit.objects.all()
    serializer_class = ExpenseSplitSerializer
