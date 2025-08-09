from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import SignUpForm


class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy(
        "login"
    )  # Redirige a la página de login después de registrarse
    template_name = "signup.html"  # Ruta a tu plantilla de registro
