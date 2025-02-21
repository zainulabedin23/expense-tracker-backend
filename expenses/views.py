import uuid
from rest_framework import viewsets
from .models import Expense, ExpenseSplit
from .serializers import ExpenseSerializer, ExpenseSplitSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from group.models import Group, GroupMember

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
        expense.date = timezone.now()  # Set current date and time
        expense.save()
        # If expense type is 'group', create ExpenseSplit records
        if expense.type == 'group':
            splits = self.request.data.get("splits", [])
            for split in splits:
                user_id = split.get("user")  # Get user UUID
                amount = split.get("amount")
                status = split.get("status", "pending")
 
                
                try:
                    user_instance = User.objects.get(id=user_id)
                    ExpenseSplit.objects.create(
                        expense=expense, user=user_instance, amount=amount, status=status
                    )
                except User.DoesNotExist:
                    raise serializer.ValidationError(f"User with ID {user_id} does not exist.")
                
    @action(detail=False, methods=['get'], url_path='group-expenses/(?P<group_id>[^/.]+)')
    def get_group_expenses(self, request, group_id=None):
        """
        Get all expenses for a given group along with split details.
        """
        # print(f"🔍 Received group_id: {group_id}")  # Debugging

       
        try:
            group_uuid = uuid.UUID(group_id)
        except ValueError:
            return Response({"error": "Invalid group_id format. Must be a UUID."}, status=status.HTTP_400_BAD_REQUEST)

       
        group = get_object_or_404(Group, id=group_uuid)
        

       
        expenses = Expense.objects.filter(group_id=group_uuid)
        

        
        response_data = {
            "group_id": str(group.id),
            "expenses": []
        }

        for expense in expenses:
            splits = ExpenseSplit.objects.filter(expense=expense).select_related("user")

            split_details = [
                {
                    "user_id": str(split.user.id),
                    "username": split.user.username,
                    "amount": split.amount,
                    "status": split.status
                }
                for split in splits
            ]

            response_data["expenses"].append({
                
                "expense_id": str(expense.id),
                "owner":str(expense.owner.username),
                "amount": float(expense.amount),
                "category": expense.category,
                "description": expense.description,
                "payment_date": expense.payment_date,
                "splits": split_details
            })

        return Response(response_data)
    
class ExpenseSplitViewSet(viewsets.ModelViewSet):
    queryset = ExpenseSplit.objects.all()
    serializer_class = ExpenseSplitSerializer


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from .models import ExpenseSplit
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

User = get_user_model()

from datetime import timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import ExpenseSplit, Expense

class PendingExpensesView(APIView):
    def get(self, request, user_id=None):
        """
        Get all pending ExpenseSplits created in the last 1 day for a specific user.
        Includes owner name and group name (if applicable).
        """
        one_day_ago = timezone.now() - timedelta(days=1)


        # Validate user ID
        user = get_object_or_404(User, id=user_id)

        # Filter pending expenses for the user
        pending_expenses = ExpenseSplit.objects.filter(
            user=user, status='pending', created_at__gte=one_day_ago
        ).select_related('expense', 'expense__owner', 'expense__group')  # Optimized DB queries

        # Serialize data
        pending_expenses_data = [
            {
                #'expense_id': expense.expense.id,
                #'user_id': expense.user.id,
                "owner_name": expense.expense.owner.username,
                "expense_description": expense.expense.description,  # Expense description
                
                'amount': expense.amount,
                'status': expense.status,
                #"user_name": expense.user.username,  # User's name
                #"user_email": expense.user.email,  # User's email
                "group_name": expense.expense.group.name if expense.expense.group else None,
            }
            for expense in pending_expenses
        ]

        return Response(pending_expenses_data, status=status.HTTP_200_OK)
from group.models import Group
from .serializers import ExpenseSerializer


class UserExpensesViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, user_id=None):
        """
        Get all expenses created by a specific user (owner) with group names instead of IDs.
        """
        user = get_object_or_404(User, id=user_id)
        expenses = Expense.objects.filter(owner=user).select_related('group')

        # Convert data to include group name
        serialized_expenses = []
        for expense in expenses:
            expense_data = ExpenseSerializer(expense).data
            # Fetch group name if group exists
            expense_data['group_name'] = expense.group.name if expense.group else "No Group"
            del expense_data['group']  # Remove group ID if not needed
            serialized_expenses.append(expense_data)

        return Response(serialized_expenses)



    
from collections import defaultdict
# import networkx as nx






class SimplifyDebtView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, group_id):
        # Validate group_id
        try:
            group_uuid = uuid.UUID(str(group_id))
        except ValueError:
            return Response({"error": "Invalid group_id format. Must be a UUID."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the group
        group = get_object_or_404(Group, id=group_uuid)

        # Fetch expenses related to the group
        expenses = Expense.objects.filter(group_id=group_uuid)

        # Step 1: Collect transactions (lender -> borrower -> amount)
        transactions = []

        for expense in expenses:
            lender_id = str(expense.owner.id)  # The owner is the lender
            splits = ExpenseSplit.objects.filter(expense=expense).select_related("user")

            for split in splits:
                if split.status.lower()=='paid':
                    continue
                borrower_id = str(split.user.id)  # The user in split is the borrower
                amount = float(split.amount)  # The amount borrowed

                if lender_id != borrower_id:  # Ignore if lender is paying themselves
                    transactions.append((borrower_id, lender_id, amount))
        # print(transactions)
        # Step 2: Simplify the transactions
        simplified_transactions = self.simplify_debts(transactions)

        return Response({"group_id": group_id, "simplified_debts": simplified_transactions})

 
   
    
    def simplify_debts(self, transactions):
        balance = defaultdict(float)

        # Calculate net balance for each user
        for borrower, lender, amount in transactions:
            balance[borrower] -= amount
            balance[lender] += amount

        # Separate creditors (positive balance) and debtors (negative balance)
        creditors = sorted([(user, amount) for user, amount in balance.items() if amount > 0], key=lambda x: x[1])
        debtors = sorted([(user, -amount) for user, amount in balance.items() if amount < 0], key=lambda x: x[1])

        # Step 3: Match debtors to creditors
        simplified_transactions = []
        i, j = 0, 0

        while i < len(debtors) and j < len(creditors):
            debtor, debt_amount = debtors[i]
            creditor, credit_amount = creditors[j]

            amount = min(debt_amount, credit_amount)
            simplified_transactions.append({"debtor": debtor, "creditor": creditor, "amount": amount})

            # Update remaining balances
            debtors[i] = (debtor, debt_amount - amount)
            creditors[j] = (creditor, credit_amount - amount)

            if debtors[i][1] == 0:
                i += 1
            if creditors[j][1] == 0:
                j += 1

        return simplified_transactions


from django.http import JsonResponse
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncDate, TruncYear

# 1️⃣ Category-wise Expense (Daily)
def category_expense_daily_api(request):
    user_id = request.GET.get('user_id')  # Get the user_id from query params
    if not user_id:
        return JsonResponse({"error": "user_id is required"}, status=400)

    expenses = (
        Expense.objects.filter(owner=user_id)
        .annotate(date=TruncDate("payment_date"))  # Grouping by daily payment_date
        .values("date", "category")
        .annotate(total_spent=Sum("amount"))
        .order_by("date")
    )
    return JsonResponse({"daily_category_expenses": list(expenses)})


# 1️⃣ Category-wise Expense (Monthly)
def category_expense_monthly_api(request):
    user_id = request.GET.get('user_id')  # Get the user_id from query params
    if not user_id:
        return JsonResponse({"error": "user_id is required"}, status=400)

    expenses = (
        Expense.objects.filter(owner=user_id)
        .annotate(month=TruncMonth("payment_date"))  # Truncate to month
        .values("month", "category")  # Only select month and category
        .annotate(total_spent=Sum("amount"))
        .order_by("month")
    )
    return JsonResponse({"monthly_category_expenses": list(expenses)})

# 2️⃣ Category-wise Expense (Yearly)
def category_expense_yearly_api(request):
    user_id = request.GET.get('user_id')  # Get the user_id from query params
    if not user_id:
        return JsonResponse({"error": "user_id is required"}, status=400)

    expenses = (
        Expense.objects.filter(owner=user_id)
        .annotate(year=TruncYear("payment_date"))  # Truncate to year
        .values("year", "category")  # Only select year and category
        .annotate(total_spent=Sum("amount"))
        .order_by("year")
    )
    return JsonResponse({"yearly_category_expenses": list(expenses)})


