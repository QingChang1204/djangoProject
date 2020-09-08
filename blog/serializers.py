from rest_framework.serializers import ModelSerializer
from blog.models import BlogUser, Article


class BlogUserSerializers(ModelSerializer):
    # 设计新的用户序列化器

    class Meta:
        model = BlogUser
        fields = [
            'username', 'email', 'display_account', 'icon', 'description', 'password'
        ]

    def create(self, validated_data):
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            instance.__setattr__(k, v)
        instance.save()
        return instance


class ArticleSerializers(ModelSerializer):
    # todo 用户的头像 姓名

    class Meta:
        model = Article
        fields = [
            'content', 'title', 'tag', 'datetime_created', 'category', 'datetime_update', 'user_id'
        ]
        depth = 1

    def create(self, validated_data):
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            instance.__setattr__(k, v)
        instance.save()
        return instance
