import uuid
from django.db import models
from django.contrib.auth import get_user_model
from group.models import Group
User = get_user_model()
class Expense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=10, choices=[('personal', 'Personal'), ('group', 'Group')])
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')  # User who created it
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='expenses') 
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='pending')  # pending, paid, etc.
    is_paid_by_user = models.UUIDField(null=True, blank=True)  # Optional, who paid for the group
    def __str__(self):
        return f"{self.owner.username} - {self.amount} ({self.type})"
class ExpenseSplit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='splits')  # Linked to Expense
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='split_expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')  # pending, paid, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.status})"