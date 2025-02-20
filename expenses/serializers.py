from rest_framework import serializers
from .models import Expense, ExpenseSplit
from users.models import User  # Assuming there's a User model

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id', 'type', 'owner', 'group', 'amount', 'category', 'description', 'payment_date', 'created_at', 'total_paid', 'status', 'is_paid_by_user']

class ExpenseSplitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseSplit
        fields = ['id', 'expense', 'user', 'amount', 'status']


 