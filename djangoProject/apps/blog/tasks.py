from __future__ import absolute_import, unicode_literals

from celery import shared_task
from celery.schedules import crontab
from django.db.models import Q
from rest_framework import serializers
from djangoProject.celery import app as current_app
from blog.models import Reply, ArticleImages
from blog.utils import es_search, logger, robot_send_alert


class ArticleImagesSerializers(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = ArticleImages
        fields = [
            'image', 'id'
        ]


@current_app.task(name='blog_signal.search_article')
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


@current_app.task(name='blog_signal.delete_attached_picture')
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


@current_app.task(name='blog_signal.delete_reply')
def delete_reply(instance_id):
    """
    移除关联回复
    :param instance_id:
    :return:
    """
    Reply.objects.filter(
        comment_id=instance_id
    ).delete()


@current_app.task(name='blog_signal.synchronous_username')
def synchronous_username(old_username, new_username):
    """
    搜索引擎搜索内容同步用户名修改
    :param old_username:
    :param new_username:
    :return:
    """
    es_search.update_search_by_author(old_username, new_username)


@current_app.task(name='blog_signal.set_attached_picture')
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


@shared_task(
    run_every=(crontab(minute=0, hour=8)), ignore_result=True, name='blog_daily.morning_message'
)
def morning_message():
    robot_send_alert(
        title="早安",
        content="早安，打工人！",
    )


@shared_task(
    run_every=(crontab(minute=0, hour=23)), ignore_result=True, name='blog_daily.night_message'
)
def night_message():
    robot_send_alert(
        title="晚安",
        content="晚安，打工人！",
    )
