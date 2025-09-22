from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django import forms

class LoginForm(AuthenticationForm):
    # Just styling; built-in validation stays intact
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "class": "form-control", "placeholder": "Username", "autocomplete": "username",
        })
        self.fields["password"].widget.attrs.update({
            "class": "form-control", "placeholder": "Password", "autocomplete": "current-password",
        })

class ChangePasswordForm(PasswordChangeForm):
    class Meta:
        model = User
        fields = ["old_password", "new_password1", "new_password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget.attrs.update({
            "class": "form-control", "placeholder": "Current password", "autocomplete": "current-password",
        })
        self.fields["old_password"].label = ""

        self.fields["new_password1"].widget.attrs.update({
            "class": "form-control", "placeholder": "New password", "autocomplete": "new-password",
        })
        self.fields["new_password1"].label = ""  # let Django render built-in password rules

        self.fields["new_password2"].widget.attrs.update({
            "class": "form-control", "placeholder": "Confirm new password", "autocomplete": "new-password",
        })
        self.fields["new_password2"].label = ""