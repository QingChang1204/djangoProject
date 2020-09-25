from rest_framework import serializers
from blog.models import User, Article, Category, Reply, Comment, AttachedPicture


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
        try:
            password = validated_data.pop('password')
        except KeyError:
            pass
        else:
            instance.set_password(password)
        for k, v in validated_data.items():
            instance.__setattr__(k, v)
        instance.save()
        return instance


class UserSerializerMixin:

    @staticmethod
    def get_user_info(obj):
        instance = User.objects.filter(
            id=obj.user_id
        ).only('icon', 'username').first()
        if instance is not None:
            return {
                "icon": instance.icon,
                "username": instance.username
            }
        else:
            return None


class CategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "category"
        ]

    def create(self, validated_data):
        instance, create_status = self.Meta.model.objects.get_or_create(category=validated_data['category'])
        instance.save()
        return instance


class AttachedPictureSerializers(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        self.old_instance_id_list = []
        self.new_instance_id_list = []
        self.__class__.old_instance_id_list = self.old_instance_id_list
        self.attached_table = kwargs.pop('attached_table', None)
        self.attached_id = kwargs.pop('attached_id', None)
        super(AttachedPictureSerializers, self).__init__(*args, **kwargs)

    def get_old_instance_id_list(self):
        return self.old_instance_id_list

    class Meta:
        model = AttachedPicture
        fields = [
            'image', 'id'
        ]

    def create(self, validated_data):
        pic_id = validated_data.pop('id', None)
        if pic_id is not None:
            self.old_instance_id_list.append(pic_id)
            pass
        else:
            instance = self.Meta.model(
                **validated_data,
                attached_id=self.attached_id,
                attached_table=self.attached_table
            )
            instance.save()
            self.new_instance_id_list.append(instance.id)
            return instance

    def remove_old_instance(self):
        self.Meta.model.objects.stealth_delete(
            attached_id=self.attached_id,
            attached_table=self.attached_table,
            old_id_list=self.old_instance_id_list + self.new_instance_id_list
        )
        self.old_instance_id_list = []
        self.new_instance_id_list = []


class ArticleSerializersMixin:

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

    @staticmethod
    def get_category_name(obj):
        instance = Category.objects.filter(
            id=obj.category_id
        ).only('category').first()
        if instance is not None:
            return instance.category
        else:
            return None


class SimpleArticleSerializers(serializers.ModelSerializer, ArticleSerializersMixin, UserSerializerMixin):
    attached_pictures = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField(read_only=True)
    user_info = serializers.SerializerMethodField(read_only=True)
    datetime_created = serializers.DateTimeField(format='%Y年%m月%d日 %H时:%M分:%S秒', read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'user_info', 'title', 'category_name', 'attached_pictures', 'datetime_created'
        ]
        read_only_fields = ['id', 'title', 'datetime_created']


class ReplySerializers(serializers.ModelSerializer, UserSerializerMixin):
    comment_id = serializers.IntegerField(write_only=True)
    user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()
    datetime_created = serializers.DateTimeField(format='%Y年%m月%d日 %H时:%M分:%S秒', read_only=True)
    user_info = serializers.SerializerMethodField(read_only=True)
    to_user_info = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_to_user_info(obj):
        instance = User.objects.filter(
            id=obj.to_user_id
        ).only('username', 'icon').first()
        if instance is not None:
            return {
                "name": instance.username,
                "icon": instance.icon
            }
        else:
            return None

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
    replies = ReplySerializers(many=True, read_only=True)
    datetime_created = serializers.DateTimeField(format='%Y年%m月%d日 %H时:%M分:%S秒', read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'user_id', 'user_info', 'article_id',
            'content', 'replies', 'datetime_created'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        instance = self.Meta.model(
            **validated_data
        )
        instance.save()
        return instance


class MyArticleSerializers(serializers.ModelSerializer, ArticleSerializersMixin):
    attached_pictures = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField(read_only=True)
    datetime_update = serializers.DateTimeField(format='%Y年%m月%d日 %H时:%M分:%S秒', read_only=True)
    publish_status = serializers.BooleanField(write_only=True)
    comments = CommentSerializers(many=True, read_only=True)
    datetime_created = serializers.DateTimeField(format='%Y年%m月%d日 %H时:%M分:%S秒', read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'attached_pictures',
            'category_name', 'publish_status', 'content',
            'tag', 'datetime_created', 'datetime_update', 'comments'
        ]
        read_only_fields = fields


class ArticleSerializers(SimpleArticleSerializers, ArticleSerializersMixin):
    attached_pictures = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField(read_only=True)
    datetime_update = serializers.DateTimeField(format='%Y年%m月%d日 %H时:%M分:%S秒', read_only=True)
    publish_status = serializers.BooleanField(write_only=True)
    comments = CommentSerializers(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        self.Meta = super(ArticleSerializers, self).Meta
        self.Meta.fields += [
            'category_name', 'publish_status', 'content',
            'tag', 'datetime_update', 'comments'
        ]
        self.Meta.read_only_fields = ['datetime_created', 'datetime_update', 'id']
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        instance = self.Meta.model(
            **validated_data,
            user_id=self.context['user_id'],
            category_id=self.context['category_id']
        )
        instance.save()
        if self.initial_data.get('images', False):
            image_serializers = AttachedPictureSerializers(
                data=self.initial_data['images'],
                many=True,
                attached_table="article",
                attached_id=instance.id
            )
            image_serializers.is_valid(raise_exception=True)
            image_serializers.save()
            if image_serializers.child.get_old_instance_id_list:
                image_serializers.child.remove_old_instance()

        return instance

    def update(self, instance, validated_data):
        if self.initial_data.get('images', False):
            image_serializers = AttachedPictureSerializers(
                data=self.initial_data['images'],
                many=True,
                attached_table="article",
                attached_id=instance.id
            )
            image_serializers.is_valid(raise_exception=True)
            image_serializers.save()
            if image_serializers.child.get_old_instance_id_list:
                image_serializers.child.remove_old_instance()

        for k, v in validated_data.items():
            instance.__setattr__(k, v)
        instance.save()
        return instance
