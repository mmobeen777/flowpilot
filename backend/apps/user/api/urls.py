from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from .views import CustomTokenObtainPairView, CreateView, DetailView, PasswordResetView

urlpatterns = [
    path("/register", CreateView.as_view(), name="register"),
    path("/detail/<str:id>", DetailView.as_view(), name="detail"),
    path("/reset-password", PasswordResetView.as_view(), name="reset-password"),
    path("/login", CustomTokenObtainPairView.as_view(), name="login"),
    path("/refresh-token", TokenRefreshView.as_view(), name="refresh-token"),
    path("/logout", TokenBlacklistView.as_view(), name="logout")
]
