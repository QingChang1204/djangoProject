from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from blog.models import User, Article, Category, Reply, Comment


class BlogUserSerializers(ModelSerializer):
    # 设计新的用户序列化器

    class Meta:
        model = User
        fields = [
            'username', 'email', 'display_account', 'icon', 'description', 'password'
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


class CategorySerializers(ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "category"
        ]

    def create(self, validated_data):
        instance, create_status = self.Meta.model.objects.get_or_create(category=validated_data['category'])
        instance.save()
        return instance


class ArticleSerializers(ModelSerializer):
    # 嵌套序列化器
    category_name = serializers.CharField(source="category.category", read_only=True)
    icon = serializers.URLField(source='user.icon', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    display_account = serializers.CharField(source='user.display_account', read_only=True)
    datetime_created = serializers.DateTimeField(format='%Y/%m/%d %H:%M:%S', read_only=True)
    datetime_update = serializers.DateTimeField(format='%Y/%m/%d %H:%M:%S', read_only=True)

    class Meta:
        model = Article
        fields = [
            'title', 'content', 'tag', 'category_name', 'icon', 'username', 'display_account',
            'datetime_created', 'datetime_update', 'id'
        ]
        read_only_fields = ['datetime_created', 'datetime_update', 'id']

    def create(self, validated_data):
        instance = self.Meta.model(
            **validated_data,
            user_id=self.context.get('user_id'),
            category_id=self.context.get('category_id')
        )
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            instance.__setattr__(k, v)
        instance.save()
        return instance


class ReplySerializers(ModelSerializer):
    comment_id = serializers.IntegerField(write_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField()
    user_icon = serializers.URLField(source='user.icon', read_only=True)
    to_username = serializers.CharField(source='to_user.username', read_only=True)
    to_user_id = serializers.IntegerField()
    to_user_icon = serializers.URLField(source='to_user.icon', read_only=True)
    datetime_created = serializers.DateTimeField(format='%Y/%m/%d %H:%M:%S', read_only=True)

    class Meta:
        model = Reply
        fields = [
            "user_id", "username", "user_icon", "to_user_id", "to_username", "to_user_icon",
            'content', "datetime_created", "comment_id"
        ]

    def create(self, validated_data):
        instance = self.Meta.model(
            **validated_data
        )
        instance.save()
        return instance


class CommentSerializers(ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField()
    article_id = serializers.IntegerField(write_only=True)
    reply = ReplySerializers(many=True, read_only=True)
    datetime_created = serializers.DateTimeField(format='%Y/%m/%d %H:%M:%S', read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'user_id', 'username', 'content', 'datetime_created',
            'reply', 'article_id'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        instance = self.Meta.model(
            **validated_data
        )
        instance.save()
        return instance
