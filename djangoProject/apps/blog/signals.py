from django.db.models.signals import post_save
from django.dispatch import receiver
from blog.models import Article
from blog.utils import search


@receiver(post_save, sender=Article)
def search_article(instance, **kwargs):
    search_word = instance.content + instance.title
    if instance.tag is not None:
        search_word += instance.tag
    search.handle_search(instance.id, search_word, instance.publish_status)
