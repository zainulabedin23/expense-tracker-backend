from django.shortcuts import render

from rest_framework import generics, permissions
from .models import Expense
from .serializers import ExpenseSerializer

# ✅ List all expenses or Create a new expense
class ExpenseListCreateView(generics.ListCreateAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)  # Set the owner to the logged-in user

# ✅ Retrieve, Update, or Delete a single expense
class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]