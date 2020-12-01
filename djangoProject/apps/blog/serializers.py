from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch, Count
from rest_framework import serializers
from rest_framework.utils import model_meta
from blog.models import User, Article, Category, Reply, Comment, ArticleImages, Tag
from blog.tasks import set_attached_picture


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
        try:
            img_list = [{"id": image.id, "image": image.image} for image in obj.images.all()]
            return img_list
        except ObjectDoesNotExist:
            return []


class CategorySerializersMixin:

    @staticmethod
    def get_category_name(obj):
        try:
            return obj.category.category
        except ObjectDoesNotExist:
            return None


class ReplySerializers(serializers.ModelSerializer, UserSerializerMixin):
    comment_id = serializers.IntegerField(write_only=True)
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
    article_id = serializers.IntegerField(write_only=True)
    reply = serializers.SerializerMethodField(read_only=True)
    reply_count = serializers.SerializerMethodField(read_only=True)
    datetime_created = serializers.DateTimeField(format='%Y年%m月%d日 %H时:%M分:%S秒', read_only=True)

    @classmethod
    def get_instance(cls):
        return cls.Meta.model.objects.select_related('user').prefetch_related(
            Prefetch('replies', queryset=Reply.objects.only(
                'to_user__icon', 'to_user__username', 'user__username', 'comment_id'
            ))
        ).annotate(
            reply_count=Count(
                'reply'
            )
        ).only(
            'user__icon', 'user__username', 'datetime_created', 'article_id', 'user_id', 'content'
        )

    @staticmethod
    def get_reply_count(obj):
        return obj.reply_count

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
            'content', 'reply_count', 'reply', 'datetime_created',
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
        'publish_status', 'content',
        'tag', 'datetime_update', 'user_id',
    ]
    read_only_fields = ['datetime_created', 'datetime_update', 'id', 'user_id']
    extra_kwargs = {'publish_status': {'write_only': True}}


class TagMixin:

    @staticmethod
    def get_tags(obj):
        info_list = []
        try:
            for i in obj.tag.all():
                info_list.append(i.content)
        except ObjectDoesNotExist:
            pass
        finally:
            return info_list


class ArticleSerializers(serializers.ModelSerializer, AttachedSerializersMixin, UserSerializerMixin,
                         CategorySerializersMixin, TagMixin):
    tags = serializers.SerializerMethodField(read_only=True)
    attached_pictures = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField(read_only=True)
    datetime_update = serializers.DateTimeField(format='%Y年%m月%d日 %H时:%M分:%S秒', read_only=True)
    user_info = serializers.SerializerMethodField(read_only=True)
    datetime_created = serializers.DateTimeField(format='%Y年%m月%d日 %H时:%M分:%S秒', read_only=True)
    tag = serializers.ListField(write_only=True)

    class Meta(ArticleMeta):
        pass

    def create(self, validated_data):
        try:
            validated_data['tag'] = Tag.objects.filter(pk__in=validated_data.get('tag', [])).all()
        except ValueError:
            validated_data.pop('tag')

        info = model_meta.get_field_info(self.Meta.model)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in validated_data):
                many_to_many[field_name] = validated_data.pop(field_name)
        instance = self.Meta.model(
            **validated_data,
        )
        instance.save()
        if self.initial_data.get('images', None) is not None:
            set_attached_picture.delay(self.initial_data['images'], "article", instance.id)
        if many_to_many:
            for field_name, value in many_to_many.items():
                field = getattr(instance, field_name)
                field.set(value)

        return instance

    def update(self, instance, validated_data):
        try:
            validated_data['tag'] = Tag.objects.filter(pk__in=validated_data.get('tag', [])).all()
        except ValueError:
            validated_data.pop('tag')

        info = model_meta.get_field_info(instance)
        update_fields = []
        m2m_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                update_fields.append(attr)
                setattr(instance, attr, value)

        if self.initial_data.get('images', None) is not None:
            set_attached_picture.delay(self.initial_data['images'], "article", instance.id)

        instance.save(update_fields=update_fields)
        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            field.set(value)
        return instance


class SimpleArticleSerializer(ArticleSerializers, TagMixin):
    tags = serializers.SerializerMethodField(read_only=True)

    @classmethod
    def get_instance(cls):
        return cls.Meta.model.objects.select_related(
            'category'
        ).prefetch_related(
                Prefetch('images', queryset=ArticleImages.objects.only(
                    'id', 'image', 'article_id'
                )), Prefetch('tag')
            ).only(
            'id', 'title', 'datetime_created', 'content', 'tag',
            'datetime_update', 'category__category'
        )

    class Meta(ArticleMeta):
        fields = [
            'id', 'title', 'attached_pictures', 'datetime_created',
            'category_name', 'content', 'tags', 'datetime_update'
        ]


class SimpleArticleUserSerializer(ArticleSerializers, TagMixin):
    tags = serializers.SerializerMethodField(read_only=True)

    @classmethod
    def get_instance(cls):
        return cls.Meta.model.objects.select_related(
            'user', 'category',
        ).prefetch_related(
            Prefetch('images', queryset=ArticleImages.objects.only(
                'id', 'image', 'article_id'
            )), Prefetch(
                'tag'
            )
        ).only(
            'id', 'title', 'user__icon', 'user__username',
            'category__category', 'datetime_created', 'tag'
        )

    class Meta(ArticleMeta):
        fields = [
            'id', 'user_info', 'title', 'category_name', 'attached_pictures',
            'datetime_created', 'tags'
        ]


class CommonArticleSerializer(ArticleSerializers):
    class Meta(ArticleMeta):
        fields = [
            'user_info', 'id', 'title', 'category_name', 'attached_pictures', 'datetime_created',
            'publish_status', 'content',
            'tag', 'datetime_update', 'user_id',
        ]


class ActivityArticleSerializer(ArticleSerializers):
    class Meta(ArticleMeta):
        fields = [
            'id', 'title'
        ]
        extra_kwargs = {'publish_status': {'write_only': True}, 'user_info': {'write_only': True}}


class ActivityCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = [
            'id', 'content'
        ]
