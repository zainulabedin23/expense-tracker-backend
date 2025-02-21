from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExpenseViewSet, ExpenseSplitViewSet
from .views import PendingExpensesView
from .views import UserExpensesViewSet,SimplifyDebtView
from .views import (
    category_expense_daily_api,
    category_expense_monthly_api,
    category_expense_yearly_api,
    SettleSplitExpenseView
)

router = DefaultRouter()
router.register(r'expenses', ExpenseViewSet)
router.register(r'expense-splits', ExpenseSplitViewSet)

urlpatterns = [
    path('expense/', include(router.urls)),
    #path('pending-expenses/<uuid:user_id>/', PendingExpensesView.as_view(), name='pending-expenses'),
    path("pending-expenses/<uuid:user_id>/", PendingExpensesView.as_view(), name="pending-expenses"),
    path('user-expenses/<uuid:user_id>/', UserExpensesViewSet.as_view({'get': 'list'}), name='user-expenses'),
    path("user-expenses/category/daily/", category_expense_daily_api, name="category_expense_daily_api"),
    path("user-expenses/category/monthly/", category_expense_monthly_api, name="category_expense_monthly_api"),
    path("user-expenses/category/yearly/", category_expense_yearly_api, name="category_expense_yearly_api"),
    path('simplify-debts/<uuid:group_id>/', SimplifyDebtView.as_view(), name='simplify-debts'),
    path("settle/", SettleSplitExpenseView.as_view(), name="settle-split-expense"),
]
    


