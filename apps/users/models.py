from django.db.models.manager import BaseManager

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from unidecode import unidecode
from django.template import defaultfilters
from django_ckeditor_5.fields import CKEditor5Field

from apps.core.models import TimeStampedModel
from apps.users.managers import UserManager
from apps.users.validators import phone_validator
from apps.users.choices import *
from apps.location.models import *


class User(AbstractUser):
    username_validator = UnicodeUsernameValidator()

    class Gender(models.TextChoices):
        MALE = "male", _("Male")
        FEMALE = "female", _("Female")

    _id = models.IntegerField(unique=True, db_index=True, null=True)
    first_name = models.CharField(max_length=64, verbose_name=_("First name"))
    last_name = models.CharField(max_length=64, verbose_name=_("Last name"))
    middle_name = models.CharField(max_length=64, null=True, blank=True, verbose_name=_("Middle name"))
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name=_("Email"))
    bio = models.TextField(null=True, blank=True, verbose_name=_("Bio"))
    date_of_birth = models.DateField(null=True, blank=True, verbose_name=_("Date of birth"))
    gender = models.CharField(max_length=12, choices=Gender.choices, verbose_name=_("Gender"), null=True, blank=True)
    username = models.CharField(
        _("username"),
        null=True,
        blank=True,
        max_length=150,
        unique=True,
        validators=[username_validator],
        error_messages={
            "unique": _("Имя пользователя уже занято."),
        },
    )

    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def save(self, *args, **kwargs):
        if not self._id and self.id is not None:
            self._id = 9999 + self.id
        if not self.username:
            self.username = None
        if not self.email:
            self.email = None
        return super().save(*args, **kwargs)

    @property
    def age(self):
        """
        Return age using `date_of_birth`
        """
        today = timezone.now().today()
        if self.date_of_birth:
            return (today.year - self.date_of_birth.year) - int(
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name}"


class TelegramUser(TimeStampedModel):
    first_name = models.CharField(max_length=200, verbose_name=_('First name'), null=True, blank=True)
    last_name = models.CharField(max_length=200, verbose_name=_('Last name'), null=True, blank=True)
    username = models.CharField(max_length=200, verbose_name=_('Username'), null=True, blank=True)
    chat_id = models.CharField(max_length=200, verbose_name=_('Chat id'))
    language_code = models.CharField(max_length=10, verbose_name=_('Language code'), null=True, blank=True)
    type = models.CharField(max_length=20, verbose_name=_('Type'), choices=TYPE_CHOICES)
    name = models.CharField(max_length=200, verbose_name=_('Name'), null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, verbose_name=_('Phone number'),
                                    validators=[phone_validator], null=True, blank=True)
    is_admin = models.BooleanField(default=False, verbose_name=_('Admin'))
    status = models.CharField(max_length=100, verbose_name=_('Status'), choices=STATUS_CHOICES,
                              default=STATUS_CHOICES[0][0])
    is_white_list = models.BooleanField(default=False, verbose_name=_("White list"))
    age = models.PositiveIntegerField(verbose_name=_("Age"))
    village = models.ForeignKey(Village, on_delete=models.PROTECT, related_name='user_village')
    job_position = models.CharField(max_length=400, verbose_name=_('Job/Study place and Position'))

    # objects = BaseManager()

    class Meta:
        verbose_name = _('TelegramUser')
        verbose_name_plural = _('TelegramUsers')

    def __str__(self):
        return f"{self.name}"


class RegistrationData(models.Model):
    chat_id = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    phone_number = models.CharField(max_length=15, validators=[phone_validator], null=True, blank=True)
    age = models.PositiveIntegerField(verbose_name=_("Age"), null=True, blank=True)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='reg_region', null=True, blank=True)
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name='reg_area', null=True, blank=True)
    village = models.ForeignKey(Village, on_delete=models.PROTECT, related_name='reg_village', null=True, blank=True)
    job_position = models.CharField(max_length=400, verbose_name=_('Job/Study place and Position'), null=True,
                                    blank=True)

    def __str__(self):
        return f"{self.name}"


class Channels(TimeStampedModel):
    username = models.CharField(max_length=123, verbose_name=_('username'),
                                help_text=" @'siz (Misol: alisher_sadullaev)")
    is_active = models.BooleanField(default=True, verbose_name=_('active'))
    order = models.PositiveIntegerField(default=0, blank=False, null=False)

    class Meta:
        verbose_name = _('channel')
        verbose_name_plural = _('channels')
        ordering = ['order']

    def __str__(self):
        return f"{self.username}"


class Info(TimeStampedModel):
    title = models.CharField(max_length=120, verbose_name=_("Title"))
    slug = models.SlugField(unique=True, blank=True, verbose_name=_('Slug'))
    content = CKEditor5Field(verbose_name=_("Content"), config_name="default")

    class Meta:
        verbose_name = _("info")
        verbose_name_plural = _("infos  ")

    def save(self, *args, **kwargs):
        self.slug = defaultfilters.slugify(unidecode(self.title))
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title}"
