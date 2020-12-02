import datetime
import time
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.utils import timezone
import hashids

# Create your models here.


class AbstractUser(AbstractBaseUser):
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


class User(AbstractUser):
    display_account = models.CharField(
        max_length=20,
        null=True
    )
    icon = models.URLField(
        help_text="用户头像",
        null=True
    )
    phone = models.CharField(
        help_text="手机号",
        null=True,
        unique=True,
        max_length=11
    )
    datetime_noticed = models.DateTimeField(
        help_text="通知时间",
        null=True
    )

    def __str__(self):
        return self.username

    def save(self, **kwargs):
        hasher = hashids.Hashids(salt=self.username)
        self.display_account = hasher.encode(int(time.time()))
        self.last_login = timezone.now()
        super(User, self).save(**kwargs)


class Activity(models.Model):
    FAVORITE = 'F'
    LIKE = 'L'
    SAVE = 'S'
    ACTIVITY_TYPES = (
        (FAVORITE, 'Favorite'),
        (LIKE, 'Like'),
        (SAVE, 'Save')
    )
    activity_type = models.CharField(
        max_length=1,
        choices=ACTIVITY_TYPES,
        null=True
    )
    user = models.ForeignKey(
        User,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
    )
    name = models.CharField(
        max_length=20,
        db_index=True,
        null=True
    )
    content_type = models.ForeignKey(
        ContentType,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        null=True
    )
    object_id = models.PositiveIntegerField()
    activity_content = GenericForeignKey()


class Category(models.Model):
    category = models.CharField(
        help_text="目录",
        max_length=100
    )
    datetime_created = models.DateTimeField(
        help_text="创建时间",
        auto_now_add=True
    )


class Tag(models.Model):
    content = models.CharField(max_length=50, null=False, blank=False)


class Article(models.Model):
    user = models.ForeignKey(
        User,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name='articles',
        related_query_name='article'
    )
    category = models.ForeignKey(
        Category,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        null=True,
        related_name='articles',
        related_query_name='article'
    )
    content = models.TextField(
        help_text="内容"
    )
    title = models.CharField(
        help_text="文章标题",
        max_length=150
    )
    tag = models.ManyToManyField(
        Tag,
        through="TagShip"
    )
    publish_status = models.BooleanField(
        help_text="发布状态",
        default=False,
        db_index=True
    )
    datetime_created = models.DateTimeField(
        help_text="创建时间",
        auto_now_add=True
    )
    datetime_update = models.DateTimeField(
        help_text="修改时间",
        auto_now=True
    )
    activities = GenericRelation(Activity, related_query_name="article")
    info = models.JSONField(
        help_text="额外信息",
        null=True
    )

    def __str__(self):
        return self.title


class TagShip(models.Model):
    article = models.ForeignKey(
        Article,
        db_constraint=False,
        on_delete=models.CASCADE
    )
    tag = models.ForeignKey(
        Tag,
        db_constraint=False,
        on_delete=models.CASCADE
    )
    datetime_created = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'blog_tag_ship'
        unique_together = ['article', 'tag']


class ImageManager(models.Manager):
    def get_all_queryset(self):
        return super(ImageManager, self).get_queryset()

    def get_queryset(self):
        return super(ImageManager, self).get_queryset().filter(status=True)

    def stealth_delete(self, foreign_key, old_id_list=False):
        filter_objects = Q(
            Q(**foreign_key) &
            Q(status=True)
        )

        if old_id_list:
            filter_objects.add(
                ~Q(id__in=old_id_list), Q.AND
            )

        self.get_all_queryset().filter(
            filter_objects
        ).update(
            status=False
        )


class AttachedPicture(models.Model):
    image = models.URLField(
        help_text="文章图片"
    )
    status = models.BooleanField(
        default=True,
        db_index=True
    )
    objects = ImageManager()

    class Meta:
        abstract = True


class ArticleImages(AttachedPicture):
    article = models.ForeignKey(
        Article,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="images"
    )

    class Meta:
        db_table = "blog_article_images"


class Comment(models.Model):
    article = models.ForeignKey(
        Article,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name='comments',
        related_query_name='comment'
    )
    user = models.ForeignKey(
        User,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name='comments',
        related_query_name='comment'
    )
    content = models.CharField(
        help_text="评论内容",
        max_length=100
    )
    datetime_created = models.DateTimeField(
        help_text="创建时间",
        auto_now_add=True
    )
    activities = GenericRelation(Activity, related_query_name="comment")

    class Meta:
        ordering = ["-datetime_created", ]


class ReplyManager(models.Manager):
    def get_queryset(self):
        return super(ReplyManager, self).get_queryset().select_related('user', 'to_user').only(
            'user__icon', 'user__username', 'to_user__username', 'to_user__icon',
            'datetime_created', 'content', 'user_id', 'to_user_id', 'comment_id'
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
        on_delete=models.DO_NOTHING,
        related_name="replies",
        related_query_name="reply"
    )
    to_user = models.ForeignKey(
        User,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="to_replies",
        related_query_name="to_reply"
    )
    content = models.CharField(
        help_text="回复内容",
        max_length=200
    )
    datetime_created = models.DateTimeField(
        help_text="创建时间",
        auto_now_add=True
    )
    objects = ReplyManager()


class VerifyCode(models.Model):
    phone = models.CharField(
        max_length=11,
        help_text="手机号"
    )
    code = models.CharField(
        max_length=6,
        help_text="验证码",
        null=True
    )
    datetime_sent = models.DateTimeField(
        help_text="发送时间",
        null=True
    )

    def code_expired(self):
        expiration_date = self.datetime_sent \
                          + datetime.timedelta(minutes=20)
        return expiration_date <= timezone.now()

    def code_invalid(self, code):
        return self.code != code

    class Meta:
        db_table = 'blog_verify_code'


class ReceiveMessage(models.Model):
    user = models.ForeignKey(
        User,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="receive_messages",
        related_query_name="receive_message"
    )
    content = models.TextField(
        help_text="发送内容"
    )
    send_user = models.ForeignKey(
        User,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="send_messages",
        related_query_name="send_message"
    )
    datetime_send = models.DateTimeField(
        help_text="发送时间",
        auto_now_add=True
    )

    class Meta:
        db_table = "blog_receive_message"


class WebSocketTicket(models.Model):
    user = models.ForeignKey(
        User,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="web_tickets",
        related_query_name="web_ticket"
    )
    ticket = models.CharField(max_length=36, null=True)

    class Meta:
        db_table = "blog_websocket_ticket"
