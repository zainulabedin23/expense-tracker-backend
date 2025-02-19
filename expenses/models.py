import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Expense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=10, choices=[('personal', 'Personal'), ('group', 'Group')])
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    group_id = models.UUIDField(null=True, blank=True)  # Only for group expenses
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='pending')
    is_paid_by_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="paid_expenses")

    def __str__(self):
        return f"{self.owner.name} - {self.amount} - {self.status}"