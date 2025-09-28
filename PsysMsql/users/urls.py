from django.urls import path
from .views import SignUpView, PasswordChangeViewUSer

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("password_change/", PasswordChangeViewUSer.as_view(), name="password_change"),
]
