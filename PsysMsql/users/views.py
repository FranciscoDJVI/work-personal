from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.views import PasswordChangeView
from .forms import SignUpForm


class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy(
        "login"
    )  # Redirige a la página de login después de registrarse
    template_name = "signup.html"  # Ruta a tu plantilla de registro


class PasswordChangeViewUSer(PasswordChangeView):
    template_name = "password_change_form.html"

    success_url = reverse_lazy("login")
