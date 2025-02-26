from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ExpenseViewSet,
    ExpenseSplitViewSet,
    PendingExpensesView,
    UserExpensesViewSet,
    SimplifyDebtView,
    ExpenseAnalyticsView,
    SettleSplitExpenseView
)

# Set up the router for ViewSets
router = DefaultRouter()
router.register(r'expenses', ExpenseViewSet)
router.register(r'expense-splits', ExpenseSplitViewSet)

urlpatterns = [
    # Router based URLs
    path('expense/', include(router.urls)),
    
    # User expense endpoints
    path('pending-expenses/<uuid:user_id>/', PendingExpensesView.as_view(), 
         name='pending-expenses'),
    path('user-expenses/<uuid:user_id>/', UserExpensesViewSet.as_view({'get': 'list'}), 
         name='user-expenses'),
    
    # Analytics endpoints - consolidated into a single view with period parameter
    path('user-expenses/analytics/', ExpenseAnalyticsView.as_view(), 
         name='expense-analytics'),
    path('user-expenses/analytics/<str:period>/', ExpenseAnalyticsView.as_view(), 
         name='expense-analytics-period'),
    
    # Debt and settlement endpoints
    path('simplify-debts/<uuid:group_id>/', SimplifyDebtView.as_view(), 
         name='simplify-debts'),
    path('settle/', SettleSplitExpenseView.as_view(), 
         name='settle-split-expense'),
]