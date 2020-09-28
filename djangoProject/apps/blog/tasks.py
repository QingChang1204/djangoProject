from __future__ import absolute_import, unicode_literals

from celery.schedules import crontab
from rest_framework import serializers
from djangoProject.celery import app as current_app
from celery.task import Task, PeriodicTask
from blog.models import AttachedPicture, Reply
from blog.utils import es_search, logger


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


@current_app.task(name='blog_signal.search_article', base=Task)
def search_article(article_id, content, title, tag, publish_status, author):
    search_word = content + title
    if tag is not None:
        search_word += tag
    es_search.handle_search(article_id, search_word, publish_status, author)


@current_app.task(name='blog_signal.delete_attached_picture', base=Task)
def delete_attached_picture(attached_table, attached_id):
    AttachedPicture.objects.stealth_delete(
        attached_table=attached_table,
        attached_id=attached_id
    )
    es_search.delete_search(article_id=attached_id)


@current_app.task(name='blog_signal.delete_reply', base=Task)
def delete_reply(instance_id):
    Reply.objects.filter(
        comment_id=instance_id
    ).delete()


@current_app.task(name='blog_signal.synchronous_username', base=Task)
def synchronous_username(old_username, new_username):
    es_search.update_search_by_author(old_username, new_username)


@current_app.task(name='blog_signal.set_attached_picture', base=Task)
def set_attached_picture(images, attached_table, attached_id):
    image_serializers = AttachedPictureSerializers(
        data=images,
        many=True,
        attached_table=attached_table,
        attached_id=attached_id
    )
    image_serializers.is_valid(raise_exception=True)
    image_serializers.save()
    if image_serializers.child.get_old_instance_id_list:
        image_serializers.child.remove_old_instance()


@current_app.task(base=PeriodicTask, run_every=(crontab(minute=1, hour=0)), ignore_result=True, name='blog_daily.test')
def daily():
    logger.info("daily")
