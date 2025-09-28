from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.views import PasswordChangeView
from .forms import SignUpForm, StyledPasswordChangeForm


class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy("login")
    template_name = "signup.html"


class PasswordChangeViewUSer(PasswordChangeView):
    form_class = StyledPasswordChangeForm

    template_name = "password_change_form.html"

    success_url = reverse_lazy("login")
