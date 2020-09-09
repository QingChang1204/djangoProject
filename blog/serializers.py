from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from blog.models import User, Article


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


class ArticleSerializers(ModelSerializer):
    icon = serializers.URLField(source='user.icon', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    display_account = serializers.CharField(source='user.display_account', read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'content', 'title', 'tag', 'datetime_created', 'category', 'datetime_update', 'icon', 'username',
            'display_account'
        ]

    def create(self, validated_data):
        instance = self.Meta.model(**validated_data, user_id=self.context.get('user_id'))
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            instance.__setattr__(k, v)
        instance.save()
        return instance
