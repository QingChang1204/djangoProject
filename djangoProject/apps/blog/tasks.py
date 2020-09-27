from __future__ import absolute_import, unicode_literals
from blog.utils import search, logger
from celery.decorators import task, periodic_task
from celery.task.schedules import crontab
from blog.models import AttachedPicture, Reply


@task
def search_article(article_id, content, title, tag, publish_status, author):
    search_word = content + title
    if tag is not None:
        search_word += tag
    search.handle_search(article_id, search_word, publish_status, author)


@task
def delete_attached_picture(attached_table, attached_id):
    AttachedPicture.objects.stealth_delete(
        attached_table=attached_table,
        attached_id=attached_id
    )
    search.delete_search(article_id=attached_id)


@task
def delete_reply(instance_id):
    Reply.objects.filter(
        comment_id=instance_id
    ).delete()


@task
def synchronous_username(old_username, new_username):
    search.update_search_by_author(old_username, new_username)


@periodic_task(run_every=(crontab(minute=1, hour=0)), ignore_result=True)
def daily():
    logger.info("daily")
