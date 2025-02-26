import uuid
from collections import defaultdict
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncDate, TruncYear
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Expense, ExpenseSplit
from .serializers import ExpenseSerializer, ExpenseSplitSerializer
from group.models import Group, GroupMember

User = get_user_model()

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
 
    def perform_create(self, serializer):
        """
        Handles both personal and group expenses:
        - If the type is 'group', also create corresponding ExpenseSplit entries.
        """
        # Save expense with current user and time
        expense = serializer.save(owner=self.request.user)
        expense.date = timezone.now()

        # Set personal expenses as paid automatically
        if expense.type == 'personal':
            expense.status = 'paid'

        expense.save()
        self.update_user_totals(expense.owner)
        
        # Handle group expenses by creating splits
        if expense.type == 'group':
            self._create_expense_splits(expense, serializer)
    
    def _create_expense_splits(self, expense, serializer):
        """Helper method to create expense splits for group expenses"""
        splits = self.request.data.get("splits", [])
        for split in splits:
            user_id = split.get("user")
            amount = split.get("amount")
            status = split.get("status", "pending")
            
            try:
                user_instance = User.objects.get(id=user_id)
                ExpenseSplit.objects.create(
                    expense=expense, 
                    user=user_instance, 
                    amount=amount, 
                    status=status
                )
                self.update_user_totals(user_instance)
            except User.DoesNotExist:
                raise serializer.ValidationError(f"User with ID {user_id} does not exist.")

    def perform_update(self, serializer):
        """
        Updates expense and recalculates totals for affected users.
        """
        expense = serializer.save()
        self.update_user_totals(expense.owner)

        # Update all split users for group expenses
        if expense.type == 'group':
            for split in expense.splits.all():
                self.update_user_totals(split.user)

    def update_user_totals(self, user):
        """Update the user's expense totals"""
        # Calculate totals with aggregation
        expense_filters = {'owner': user}
        
        total_expense = Expense.objects.filter(**expense_filters).aggregate(
            total=Sum("amount"))["total"] or 0
            
        expense_filters['status'] = 'paid'
        total_paid = Expense.objects.filter(**expense_filters).aggregate(
            total=Sum("amount"))["total"] or 0
            
        expense_filters['status'] = 'pending'
        total_pending = Expense.objects.filter(**expense_filters).aggregate(
            total=Sum("amount"))["total"] or 0
        
        # Update user profile with calculated totals
        user.total_expenses = total_expense
        user.total_paid = total_paid
        user.total_pending = total_pending
        user.save()

    @action(detail=False, methods=['get'], url_path='group-expenses/(?P<group_id>[^/.]+)')
    def get_group_expenses(self, request, group_id=None):
        """
        Get all expenses for a given group along with split details.
        """
        try:
            group_uuid = uuid.UUID(group_id)
        except ValueError:
            return Response(
                {"error": "Invalid group_id format. Must be a UUID."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        group = get_object_or_404(Group, id=group_uuid)
        expenses = Expense.objects.filter(group_id=group_uuid)
        
        response_data = self._format_group_expenses(group, expenses)
        return Response(response_data)
    
    def _format_group_expenses(self, group, expenses):
        """Helper method to format group expenses for response"""
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
                "owner": str(expense.owner.username),
                "amount": float(expense.amount),
                "category": expense.category,
                "description": expense.description,
                "payment_date": expense.payment_date,
                "splits": split_details
            })
            
        return response_data


class ExpenseSplitViewSet(viewsets.ModelViewSet):
    queryset = ExpenseSplit.objects.all()
    serializer_class = ExpenseSplitSerializer
    permission_classes = [IsAuthenticated]


class PendingExpensesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id=None):
        """
        Get all pending ExpenseSplits for a specific user.
        If `last_day=true` is passed in query params, it filters for the last 1 day only.
        """
        user = get_object_or_404(User, id=user_id)
        
        # Start with base queryset - pending expenses for this user
        pending_expenses = ExpenseSplit.objects.filter(
            user=user, 
            status="pending"
        ).select_related("expense", "expense__owner", "expense__group")

        # Filter by date if requested
        last_day = request.GET.get("last_day")
        if last_day == "true":
            one_day_ago = timezone.now() - timedelta(days=1)
            pending_expenses = pending_expenses.filter(created_at__gte=one_day_ago)

        # Group expenses by group name
        grouped_expenses = self._group_expenses_by_group(pending_expenses)
        return Response(grouped_expenses, status=status.HTTP_200_OK)
    
    def _group_expenses_by_group(self, expenses):
        """Helper method to group expenses by group name"""
        grouped_expenses = defaultdict(list)

        for expense in expenses:
            group_name = expense.expense.group.name if expense.expense.group else "No Group"
            grouped_expenses[group_name].append({
                "split_expense_id": expense.id,
                "owner_name": expense.expense.owner.username,
                "expense_description": expense.expense.description,
                "amount": expense.amount,
                "status": expense.status,
            })
            
        return grouped_expenses


class UserExpensesViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, user_id=None):
        """
        Get all expenses created by a specific user (owner) with group names instead of IDs.
        """
        user = get_object_or_404(User, id=user_id)
        expenses = Expense.objects.filter(owner=user).select_related('group')

        serialized_expenses = []
        for expense in expenses:
            expense_data = ExpenseSerializer(expense).data
            # Replace group ID with group name
            expense_data['group_name'] = expense.group.name if expense.group else "No Group"
            del expense_data['group']  # Remove group ID
            serialized_expenses.append(expense_data)

        return Response(serialized_expenses)


class SimplifyDebtView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, group_id):
        """
        Get simplified debts for a group to minimize the number of transactions.
        """
        try:
            group_uuid = uuid.UUID(str(group_id))
        except ValueError:
            return Response(
                {"error": "Invalid group_id format. Must be a UUID."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        group = get_object_or_404(Group, id=group_uuid)
        
        # Collect transactions from all expenses in the group
        transactions = self._collect_group_transactions(group_uuid)
        
        # Simplify the debt transactions
        simplified_transactions = self._simplify_debts(transactions)

        return Response({
            "group_id": group_id, 
            "simplified_debts": simplified_transactions
        })
    
    def _collect_group_transactions(self, group_uuid):
        """Helper method to collect all transactions in a group"""
        transactions = []
        expenses = Expense.objects.filter(group_id=group_uuid)

        for expense in expenses:
            lender_id = str(expense.owner.id)
            splits = ExpenseSplit.objects.filter(expense=expense).select_related("user")

            for split in splits:
                if split.status.lower() == 'paid':
                    continue
                    
                borrower_id = str(split.user.id)
                amount = float(split.amount)

                # Only add if lender and borrower are different people
                if lender_id != borrower_id:
                    transactions.append((borrower_id, lender_id, amount))
                    
        return transactions
    
    def _simplify_debts(self, transactions):
        """
        Simplify debts to minimize the number of transactions needed.
        """
        balance = defaultdict(float)

        # Calculate net balance for each user
        for borrower, lender, amount in transactions:
            balance[borrower] -= amount
            balance[lender] += amount

        # Separate creditors and debtors
        creditors = sorted([(user, amount) for user, amount in balance.items() 
                           if amount > 0], key=lambda x: x[1])
        debtors = sorted([(user, -amount) for user, amount in balance.items() 
                         if amount < 0], key=lambda x: x[1])

        # Match debtors to creditors
        simplified_transactions = []
        i, j = 0, 0

        while i < len(debtors) and j < len(creditors):
            debtor, debt_amount = debtors[i]
            creditor, credit_amount = creditors[j]

            amount = min(debt_amount, credit_amount)
            simplified_transactions.append({
                "debtor": debtor, 
                "creditor": creditor, 
                "amount": amount
            })

            # Update remaining balances
            debtors[i] = (debtor, debt_amount - amount)
            creditors[j] = (creditor, credit_amount - amount)

            # Move to next person if their balance is zero
            if debtors[i][1] == 0:
                i += 1
            if creditors[j][1] == 0:
                j += 1

        return simplified_transactions


class ExpenseAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, period=None):
        """
        Get category-wise expense analytics for a user.
        Period can be 'daily', 'monthly', or 'yearly'.
        """
        user_id = request.GET.get('user_id')
        if not user_id:
            return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        period = period or request.GET.get('period', 'monthly')
        
        if period == 'daily':
            return self._get_daily_expenses(user_id)
        elif period == 'monthly':
            return self._get_monthly_expenses(user_id)
        elif period == 'yearly':
            return self._get_yearly_expenses(user_id)
        else:
            return Response(
                {"error": "Invalid period. Choose 'daily', 'monthly', or 'yearly'"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _get_daily_expenses(self, user_id):
        """Get daily expense analytics by category"""
        expenses = (
            Expense.objects.filter(owner=user_id)
            .annotate(date=TruncDate("payment_date"))
            .values("date", "category")
            .annotate(total_spent=Sum("amount"))
            .order_by("date")
        )
        return Response({"daily_category_expenses": list(expenses)})
    
    def _get_monthly_expenses(self, user_id):
        """Get monthly expense analytics by category"""
        expenses = (
            Expense.objects.filter(owner=user_id)
            .annotate(month=TruncMonth("payment_date"))
            .values("month", "category")
            .annotate(total_spent=Sum("amount"))
            .order_by("month")
        )
        return Response({"monthly_category_expenses": list(expenses)})
    
    def _get_yearly_expenses(self, user_id):
        """Get yearly expense analytics by category"""
        expenses = (
            Expense.objects.filter(owner=user_id)
            .annotate(year=TruncYear("payment_date"))
            .values("year", "category")
            .annotate(total_spent=Sum("amount"))
            .order_by("year")
        )
        return Response({"yearly_category_expenses": list(expenses)})


class SettleSplitExpenseView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Settles a split expense by updating its status to 'paid' 
        and creating a new personal expense under 'Settlement' category.
        """
        split_expense_id = request.data.get("split_expense_id")
        if not split_expense_id:
            return Response(
                {"error": "split_expense_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        split_expense = get_object_or_404(ExpenseSplit, id=split_expense_id)

        if split_expense.status == "paid":
            return Response(
                {"message": "This expense is already settled"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark split expense as paid
        split_expense.status = "paid"
        split_expense.save()

        try:
            # Create a settlement expense record
            new_expense = self._create_settlement_expense(split_expense)
            
            return Response(
                {
                    "message": "Split expense settled successfully",
                    "new_expense_id": new_expense.id,
                    "new_expense_description": new_expense.description,
                    "amount": new_expense.amount,
                    "group_id": new_expense.group.id if new_expense.group else None
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "Failed to create settlement expense"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _create_settlement_expense(self, split_expense):
        """Helper method to create a settlement expense record"""
        return Expense.objects.create(
            id=uuid.uuid4(),
            type="personal",
            owner=split_expense.user,
            amount=split_expense.amount,
            category="Settlement",
            description=f"Settlement for {split_expense.expense.description}",
            group=split_expense.expense.group,
            status="paid",
            payment_date=timezone.now(),
            is_paid_by_user=split_expense.user.id
        )