import time
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
import hashids

# Create your models here.


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


class User(NewAbstractUser):
    display_account = models.CharField(max_length=20, null=True)
    icon = models.URLField(verbose_name="用户头像", null=True)
    description = models.TextField(verbose_name="用户描述", null=True)
    phone = models.CharField(verbose_name="手机号", null=True, unique=True, max_length=11)

    def __str__(self):
        return self.username

    def save(self):
        hasher = hashids.Hashids(salt=self.username)
        self.display_account = hasher.encode(int(time.time()))
        self.last_login = timezone.now()
        self.set_password(self.password)
        super(User, self).save()


class Article(models.Model):
    content = models.TextField(verbose_name="内容")
    title = models.CharField(verbose_name="文章标题", max_length=150)
    user = models.ForeignKey(User, db_constraint=False, on_delete=models.DO_NOTHING)
    tag = models.CharField(verbose_name="标签", max_length=30, null=True)
    datetime_created = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    datetime_update = models.DateTimeField(verbose_name="修改时间", auto_now=True)
    category = models.CharField(verbose_name="目录", null=True, max_length=100)

    def __str__(self):
        return self.title
