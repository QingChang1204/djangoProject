import time
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
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
    display_account = models.CharField(
        max_length=20,
        null=True
    )
    icon = models.URLField(
        verbose_name="用户头像",
        null=True
    )
    description = models.TextField(
        verbose_name="用户描述",
        null=True
    )
    phone = models.CharField(
        verbose_name="手机号",
        null=True,
        unique=True,
        max_length=11
    )
    datetime_noticed = models.DateTimeField(
        verbose_name="通知时间",
        null=True
    )

    def __str__(self):
        return self.username

    def save(self):
        hasher = hashids.Hashids(salt=self.username)
        self.display_account = hasher.encode(int(time.time()))
        self.last_login = timezone.now()
        super(User, self).save()


class Category(models.Model):
    category = models.CharField(
        verbose_name="目录",
        max_length=100
    )
    datetime_created = models.DateTimeField(
        verbose_name="创建时间",
        auto_now_add=True
    )


class Article(models.Model):
    user = models.ForeignKey(
        User,
        db_constraint=False,
        on_delete=models.DO_NOTHING
    )
    category = models.ForeignKey(
        Category,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        null=True
    )
    content = models.TextField(
        verbose_name="内容"
    )
    title = models.CharField(
        verbose_name="文章标题",
        max_length=150
    )
    tag = models.CharField(
        verbose_name="标签",
        max_length=30,
        null=True
    )
    publish_status = models.BooleanField(
        verbose_name="发布状态",
        default=False
    )
    datetime_created = models.DateTimeField(
        verbose_name="创建时间",
        auto_now_add=True
    )
    datetime_update = models.DateTimeField(
        verbose_name="修改时间",
        auto_now=True
    )

    def __str__(self):
        return self.title


class ImageManager(models.Manager):
    def get_all_queryset(self):
        return super(ImageManager, self).get_queryset()

    def get_queryset(self):
        return super(ImageManager, self).get_queryset().filter(status=True)

    def stealth_delete(self, attached_id, attached_table, old_id_list):
        self.get_all_queryset().filter(
            ~Q(id__in=old_id_list),
            attached_id=attached_id,
            attached_table=attached_table,
            status=True
        ).update(
            status=False
        )


class AttachedPicture(models.Model):
    attached_id = models.IntegerField(
        verbose_name="附属ID"
    )
    attached_table = models.CharField(
        verbose_name="附属表",
        max_length=20
    )
    image = models.URLField(
        verbose_name="文章图片"
    )
    status = models.BooleanField(
        default=True
    )
    objects = ImageManager()

    class Meta:
        index_together = ["attached_id", "attached_table"]


class Comment(models.Model):
    article = models.ForeignKey(
        Article,
        db_constraint=False,
        on_delete=models.DO_NOTHING
    )
    user = models.ForeignKey(
        User,
        db_constraint=False,
        on_delete=models.DO_NOTHING
    )
    content = models.CharField(
        verbose_name="评论内容",
        max_length=200
    )
    datetime_created = models.DateTimeField(
        verbose_name="创建时间",
        auto_now_add=True
    )


class Reply(models.Model):
    comment = models.ForeignKey(
        Comment,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="replies",
        related_query_name="reply"
    )
    user = models.ForeignKey(
        User,
        db_constraint=False,
        on_delete=models.DO_NOTHING
    )
    to_user = models.ForeignKey(
        User,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="to_user"
    )
    content = models.CharField(
        verbose_name="回复内容",
        max_length=200
    )
    datetime_created = models.DateTimeField(
        verbose_name="创建时间",
        auto_now_add=True
    )
