from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django import forms


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
        )
        labels = {
            "Username": "",
            "Email": "",
        }
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "bg-gray-200 ",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "bg-gray-200 ",
                }
            ),
            "password1": forms.PasswordInput(
                attrs={
                    "class": "bg-gray-200 ",
                }
            ),
            "Password2": forms.PasswordInput(
                attrs={
                    "class": "bg-gray-200 ",
                }
            ),
        }


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["old_password"].label = "Contraseña actual"
        self.fields["new_password1"].label = "Nueva contraseña"
        self.fields["new_password2"].label = "Confirmar contraseña"

        self.fields["new_password1"].help_text = ""
        self.fields[
            "new_password2"
        ].help_text = "Escribe de nuevo tu nueva contraseña para verificación."

        self.fields["old_password"].widget.attrs.update({"class": "bg-gray-200 p-2"})
        self.fields["new_password1"].widget.attrs.update({"class": "bg-gray-200 p-2"})
        self.fields["new_password2"].widget.attrs.update({"class": "bg-gray-200 p-2"})
