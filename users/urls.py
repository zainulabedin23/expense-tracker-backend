from django.urls import path
from .views import RegisterView, LoginView, UserDetailView,RetrieveUserByEmailView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("user/", UserDetailView.as_view(), name="user-detail"),
    path("get-user-by-email/", RetrieveUserByEmailView.as_view(), name="get-user-by-email")
]
