from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin

from apps.users.forms import UserAdminChangeForm, UserAdminCreationForm
from apps.users.models import User, TelegramUser, Channels, RegistrationData, Info
from import_export.admin import ImportExportModelAdmin
from django.contrib.auth import admin as auth_admin
from django.utils.translation import gettext_lazy as _


class UserAdmin(auth_admin.UserAdmin, ImportExportModelAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "username", "gender", "date_of_birth")},
        ),
        (
            _("Other info"),
            {"fields": ("bio",)},
        ),
        (
            _("Permissions"),
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        (_("Dates"), {"fields": ("last_login", "date_joined")}),
        (None, {"fields": ("email", "password")}),
    )
    list_display = [
        "_id",
        "first_name",
        "last_name",
        "email",
        "is_superuser",
    ]
    list_filter = auth_admin.UserAdmin.list_filter
    search_fields = ["first_name", "last_name"]
    ordering = ["id"]


class TelegramUserAdmin(ImportExportModelAdmin):
    list_display = ['name', 'username', 'chat_id', 'phone_number', "age",
                    'status', 'type', 'is_admin', "is_white_list",
                    'created_at', 'language_code',
                    'first_name', 'last_name', 'id']
    list_filter = ['status', 'type', 'language_code', "is_white_list"]
    list_editable = ['is_admin', "is_white_list"]
    search_fields = ['name', 'username', 'phone_number', 'first_name', 'last_name', 'chat_id']

    fieldsets = (
        (_('Telegram Info'), {"fields": ('first_name', 'last_name', 'username', 'language_code')}),
        (_('Personal Info'), {"fields": ('name', 'phone_number', "age", "job_position")}),
        (_('Others'), {"fields": ('status', 'type')})
    )

    def has_add_permission(self, request):
        return False


class ChannelAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['username', 'is_active', 'id', "order"]
    list_editable = ['is_active']
    search_fields = ('username',)

    fieldsets = (
        (None, {"fields": ('username', 'is_active',)}),
    )


class RegisterAdmin(admin.ModelAdmin):
    list_display = ['chat_id']


class InfoAdmin(admin.ModelAdmin):
    list_display = ['slug']

    fieldsets = (
        (None, {"fields": ("title", 'content')}),
    )


admin.site.register(User, UserAdmin)
# admin.site.register(TelegramUser, TelegramUserAdmin)
# admin.site.register(Channels, ChannelAdmin)
# admin.site.register(RegistrationData, RegisterAdmin)
# admin.site.register(Info, InfoAdmin)
