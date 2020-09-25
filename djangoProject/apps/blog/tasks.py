from __future__ import absolute_import, unicode_literals
from blog.utils import search
from djangoProject.celery import app as celery_app
from blog.models import AttachedPicture, Reply


@celery_app.task
def search_article(article_id, content, title, tag, publish_status):
    search_word = content + title
    if tag is not None:
        search_word += tag
    search.handle_search(article_id, search_word, publish_status)


@celery_app.task
def delete_attached_picture(attached_table, attached_id):
    AttachedPicture.objects.stealth_delete(
        attached_table=attached_table,
        attached_id=attached_id
    )
    search.delete_search(article_id=attached_id)


@celery_app.task
def delete_reply(instance_id):
    Reply.objects.filter(
        comment_id=instance_id
    ).delete()
