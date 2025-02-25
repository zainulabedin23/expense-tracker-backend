from rest_framework import serializers
from .models import Expense, ExpenseSplit
from users.models import User  # Assuming there's a User model
from django.utils import timezone

class ExpenseSerializer(serializers.ModelSerializer):
    payment_date = serializers.DateTimeField(default=timezone.now) 

    class Meta:
        model = Expense
        fields = ['id','title', 'type', 'owner', 'group', 'amount', 'category', 'description', 'payment_date', 'created_at', 'total_paid', 'status', 'is_paid_by_user']

    def create(self, validated_data):
        request = self.context.get('request')  # Get request context
        if request and request.user:
            validated_data['owner'] = request.user  # Set owner as logged-in user
            validated_data['is_paid_by_user'] = request.user.id  # Set is_paid_by_user same as owner ID

        if 'payment_date' not in validated_data:
            validated_data['payment_date'] = timezone.now()  # Set default payment date

        return super().create(validated_data)

class ExpenseSplitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseSplit
        fields = ['id', 'expense', 'user', 'amount', 'status']
