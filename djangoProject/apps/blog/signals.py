from django.db.models.signals import pre_save, pre_delete, post_save
from django.dispatch import receiver
from blog.models import Article, Comment, Reply, AttachedPicture
from blog.utils import search


@receiver(post_save, sender=Article)
def post_search_article(instance, created, **kwargs):
    if created:
        search_word = instance.content + instance.title
        if instance.tag is not None:
            search_word += instance.tag
        search.handle_search(instance.id, search_word, instance.publish_status)


@receiver(pre_save, sender=Article)
def put_search_article(instance, update_fields, **kwargs):
    check = ['content', 'title', 'tag']
    if instance.id is not None and any([info in update_fields for info in check]):
        search_word = instance.content + instance.title
        if instance.tag is not None:
            search_word += instance.tag
        search.handle_search(instance.id, search_word, instance.publish_status)


@receiver(pre_delete, sender=Article)
def delete_article_pictures(instance, **kwargs):
    AttachedPicture.objects.stealth_delete(
        attached_table="article",
        attached_id=instance.id
    )


@receiver(pre_delete, sender=Comment)
def delete_reply(instance, **kwargs):
    Reply.objects.filter(
        comment_id=instance.id
    ).delete()
