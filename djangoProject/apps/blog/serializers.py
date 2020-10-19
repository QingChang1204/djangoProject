from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from blog.models import User, Article, Category, Reply, Comment, AttachedPicture
from blog.tasks import AttachedPictureSerializers, set_attached_picture


class BlogUserSerializers(serializers.ModelSerializer):
    # 设计新的用户序列化器
    class Meta:
        model = User
        fields = [
            'username', 'email', 'display_account', 'icon', 'password'
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        instance = self.Meta.model(**validated_data)
        instance.set_password(validated_data['password'])
        instance.save()
        return instance

    def update(self, instance, validated_data):
        update_fields = []
        try:
            password = validated_data.pop('password')
        except KeyError:
            pass
        else:
            instance.set_password(password)
        for k, v in validated_data.items():
            instance.__setattr__(k, v)
            update_fields.append(k)
        instance.save(update_fields=update_fields)
        return instance


class UserSerializerMixin:

    @staticmethod
    def get_user_info(obj):
        try:
            return {
                "icon": obj.user.icon,
                "username": obj.user.username
            }
        except ObjectDoesNotExist:
            return {
                "icon": None,
                "username": None
            }


class CategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "category"
        ]

    def create(self, validated_data):
        instance, create_status = self.Meta.model.objects.get_or_create(category=validated_data['category'])
        return instance


class AttachedSerializersMixin:

    @staticmethod
    def get_attached_pictures(obj):
        instance = AttachedPicture.objects.filter(
            attached_table="article",
            attached_id=obj.id
        ).only('image', 'id').all()

        serializer = AttachedPictureSerializers(
            instance=instance,
            many=True
        )

        return serializer.data


class CategorySerializersMixin:

    @staticmethod
    def get_category_name(obj):
        try:
            return obj.category.category
        except ObjectDoesNotExist:
            return None


class ReplySerializers(serializers.ModelSerializer, UserSerializerMixin):
    comment_id = serializers.IntegerField(write_only=True)
    user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()
    datetime_created = serializers.DateTimeField(format='%Y年%m月%d日 %H时:%M分:%S秒', read_only=True)
    user_info = serializers.SerializerMethodField(read_only=True)
    to_user_info = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_to_user_info(obj):
        return {
            "name": obj.to_user.username,
            "icon": obj.to_user.icon
        }

    class Meta:
        model = Reply
        fields = [
            "user_id", "user_info", "to_user_id", "to_user_info",
            'content', "datetime_created", "comment_id"
        ]

    def create(self, validated_data):
        instance = self.Meta.model(
            **validated_data
        )
        instance.save()
        return instance


class CommentSerializers(serializers.ModelSerializer, UserSerializerMixin):
    user_info = serializers.SerializerMethodField(read_only=True)
    user_id = serializers.IntegerField()
    article_id = serializers.IntegerField(write_only=True)
    reply = serializers.SerializerMethodField(read_only=True)
    datetime_created = serializers.DateTimeField(format='%Y年%m月%d日 %H时:%M分:%S秒', read_only=True)

    @staticmethod
    def get_reply(obj):
        return_list = []
        try:
            for reply in obj.replies.all():
                return_list.append({
                    "to_user_id": reply.to_user.username,
                    "to_user_icon": reply.to_user.icon,
                })
            return return_list
        except ObjectDoesNotExist:
            return

    class Meta:
        model = Comment
        fields = [
            'id', 'user_id', 'user_info', 'article_id',
            'content', 'reply', 'datetime_created'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        instance = self.Meta.model(
            **validated_data
        )
        instance.save()
        return instance


class ArticleMeta:
    model = Article
    fields = [
        'user_info', 'id', 'title', 'category_name', 'attached_pictures', 'datetime_created',
        'category_name', 'publish_status', 'content',
        'tag', 'datetime_update', 'user_id',
    ]
    read_only_fields = ['datetime_created', 'datetime_update', 'id', 'user_id']
    extra_kwargs = {'publish_status': {'write_only': True}}


class ArticleSerializers(serializers.ModelSerializer, AttachedSerializersMixin, UserSerializerMixin,
                         CategorySerializersMixin):
    attached_pictures = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField(read_only=True)
    datetime_update = serializers.DateTimeField(format='%Y年%m月%d日 %H时:%M分:%S秒', read_only=True)
    user_info = serializers.SerializerMethodField(read_only=True)
    datetime_created = serializers.DateTimeField(format='%Y年%m月%d日 %H时:%M分:%S秒', read_only=True)

    class Meta(ArticleMeta):
        pass

    def create(self, validated_data):
        instance = self.Meta.model(
            **validated_data,
            user=self.context['user'],
            category=self.context['category']
        )
        instance.save()
        if self.initial_data.get('images', False):
            set_attached_picture.delay(self.initial_data['images'], "article", instance.id)

        return instance

    def update(self, instance, validated_data):
        update_fields = []
        if self.initial_data.get('images', False):
            set_attached_picture.delay(self.initial_data['images'], "article", instance.id)

        if self.context.get('category', False):
            instance.category = self.context.get('category')
            update_fields.append('category')

        for k, v in validated_data.items():
            update_fields.append(k)
            instance.__setattr__(k, v)
        instance.save(update_fields=update_fields)
        return instance


class SimpleArticleSerializer(ArticleSerializers):
    class Meta(ArticleMeta):
        fields = [
            'id', 'title', 'category_name', 'attached_pictures', 'datetime_created',
            'category_name', 'publish_status', 'content',
            'tag', 'datetime_update', 'user_id', 'user_info'
        ]
        extra_kwargs = {'publish_status': {'write_only': True}, 'user_info': {'write_only': True}}


class CommonArticleSerializer(ArticleSerializers):
    class Meta(ArticleMeta):
        fields = [
            'user_info', 'id', 'title', 'category_name', 'attached_pictures', 'datetime_created',
            'category_name', 'publish_status', 'content',
            'tag', 'datetime_update', 'user_id',
        ]
