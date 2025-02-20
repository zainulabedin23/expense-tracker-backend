from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExpenseViewSet, ExpenseSplitViewSet
from .views import PendingExpensesView
from .views import UserExpensesViewSet
router = DefaultRouter()
router.register(r'expenses', ExpenseViewSet)
router.register(r'expense-splits', ExpenseSplitViewSet)

urlpatterns = [
    path('expense/', include(router.urls)),
    path('pending-expenses/<uuid:user_id>/', PendingExpensesView.as_view(), name='pending-expenses'),
    path('user-expenses/<uuid:user_id>/', UserExpensesViewSet.as_view({'get': 'list'}), name='user-expenses'),
]
