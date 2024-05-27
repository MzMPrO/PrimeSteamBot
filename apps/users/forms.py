from django.contrib.auth import forms as admin_forms
from django.contrib.auth import get_user_model
from django.forms import CharField
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User
        field_classes = {"username": CharField}


class UserAdminCreationForm(admin_forms.UserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):
        model = User
        fields = ("username",)
        field_classes = {"username": CharField}
        error_messages = {
            "username": {"unique": _("The username is already taken.")},
        }
