from __future__ import absolute_import, unicode_literals

from celery.schedules import crontab
from django.db.models import Q
from rest_framework import serializers
from djangoProject.celery import app as current_app
from celery.task import Task, PeriodicTask
from blog.models import Reply, ArticleImages
from blog.utils import es_search, logger


class ArticleImagesSerializers(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = ArticleImages
        fields = [
            'image', 'id'
        ]


@current_app.task(name='blog_signal.search_article', base=Task)
def search_article(article_id, content, title, tag, publish_status, author):
    """
    设置文章搜索词
    :param article_id:
    :param content:
    :param title:
    :param tag:
    :param publish_status:
    :param author:
    :return:
    """
    search_word = content + title
    if tag is not None:
        search_word += tag
    es_search.handle_search(article_id, search_word, publish_status, author)


@current_app.task(name='blog_signal.delete_attached_picture', base=Task)
def delete_attached_picture(attached_table, attached_id):
    """
    移除关联图片，关联词
    :param attached_table:
    :param attached_id:
    :return:
    """
    if attached_table == 'article':
        ArticleImages.objects.stealth_delete(
            foreign_key={
                'article_id': attached_id
            }
        )
        es_search.delete_search(article_id=attached_id)
    else:
        logger.info(
            "删除附属图片传输数据错误"
        )
        pass


@current_app.task(name='blog_signal.delete_reply', base=Task)
def delete_reply(instance_id):
    """
    移除关联回复
    :param instance_id:
    :return:
    """
    Reply.objects.filter(
        comment_id=instance_id
    ).delete()


@current_app.task(name='blog_signal.synchronous_username', base=Task)
def synchronous_username(old_username, new_username):
    """
    搜索引擎搜索内容同步用户名修改
    :param old_username:
    :param new_username:
    :return:
    """
    es_search.update_search_by_author(old_username, new_username)


@current_app.task(name='blog_signal.set_attached_picture', base=Task)
def set_attached_picture(images, attached_table, attached_id):
    """
    设置关联图片
    :param images:
    :param attached_table:
    :param attached_id:
    :return:
    """
    if attached_table == 'article':
        model = ArticleImages
        serializer = ArticleImagesSerializers
        extra_args = {
            "article_id": attached_id
        }
    else:
        raise Exception(
            "传输数据错误"
        )
    old_id_list = []
    old_instance = []
    new_instance = []
    if not images:
        model.objects.filter(
            **extra_args,
            status=True
        ).update(
            status=False
        )
    else:
        image_serializers = serializer(
            data=images,
            many=True
        )
        image_serializers.is_valid(raise_exception=True)

        for data in image_serializers.data:
            if data.get('id', None) is not None:
                old_instance.append(
                    model(**data, **extra_args)
                )
                old_id_list.append(data['id'])
            else:
                new_instance.append(
                    model(**data, **extra_args)
                )

        if model.objects.filter(
                ~Q(**extra_args),
                id__in=old_id_list
        ).exists():
            raise Exception(
                "非法ID"
            )
        else:
            model.objects.stealth_delete(
                foreign_key=extra_args,
                old_id_list=old_id_list
            )

            model.objects.bulk_create(
                new_instance
            )
            model.objects.bulk_update(
                old_instance,  fields=['image']
            )


@current_app.task(base=PeriodicTask, run_every=(crontab(minute=1, hour=0)), ignore_result=True, name='blog_daily.test')
def daily():
    logger.info("daily")
