from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExpenseViewSet, ExpenseSplitViewSet

router = DefaultRouter()
router.register(r'expenses', ExpenseViewSet)
router.register(r'expense-splits', ExpenseSplitViewSet)

urlpatterns = [
    path('expense/', include(router.urls)),
]
