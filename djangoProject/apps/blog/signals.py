from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from blog.models import Article, Comment, Reply
from blog.utils import search


@receiver(post_save, sender=Article)
def search_article(instance, **kwargs):
    search_word = instance.content + instance.title
    if instance.tag is not None:
        search_word += instance.tag
    search.handle_search(instance.id, search_word, instance.publish_status)


@receiver(post_delete, sender=Comment)
def delete_reply(instance, **kwargs):
    Reply.objects.filter(
        comment_id=instance.id
    ).delete()
