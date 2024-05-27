from django.utils.translation import gettext_lazy as _

STATUS_CHOICES = (
    ('active', _('Active')),
    ('blocked', _('Blocked')),
    ('not_found', _('Not found')),
    ('deactivated', _('Deactivated')),
)

TYPE_CHOICES = (
    ('private', _('Private')),
    ('group', _("Group")),
    ('supergroup', _("Super group")),
    ('chanel', _("Channel")),
)
