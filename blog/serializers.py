from rest_framework import serializers

from blog.models import BlogUser


class BlogUserSerializers(serializers.ModelSerializer):
    # 设计新的用户序列化器

    class Meta:
        model = BlogUser
        fields = [
            'username', 'email', 'display_account', 'icon', 'description', 'password'
        ]

    def create(self, validated_data):
        blog_user = self.Meta.model(**validated_data)
        blog_user.save()
        return blog_user

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            instance.__setattr__(k, v)
        instance.save()
        return instance
