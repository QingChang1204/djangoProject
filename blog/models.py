from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.core import validators
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone


# Create your models here.
from django.utils.deconstruct import deconstructible


@deconstructible
class UnicodeUsernameValidator(validators.RegexValidator):
    regex = r'^[\w.@+-]+\Z'
    message = (
        'Enter a valid username. This value may contain only letters, '
        'numbers, and @/./+/-/_ characters.'
    )
    flags = 0


class NewAbstractUser(AbstractBaseUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        max_length=100,
        unique=True,
        help_text='Required. 100 characters or fewer. Letters, digits and @/./+/-/_ only.',
        validators=[username_validator],
    )
    email = models.EmailField('邮件地址', blank=True)
    is_staff = models.BooleanField(
        '管理员权限',
        default=False,
        help_text='Designates whether the user can log into this admin site.',
    )
    is_active = models.BooleanField(
        '激活状态',
        default=True,
        help_text=(
            'Designates whether this user should be treated as active. '
        ),
    )
    datetime_created = models.DateTimeField('创建时间', default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        abstract = True

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)


class BlogUser(NewAbstractUser):
    display_account = models.CharField(max_length=12, null=False)

    def __str__(self):
        return self.username
