from django.db.models.signals import pre_save, pre_delete, post_save
from django.dispatch import receiver
from blog.models import Article, Comment, User
from blog.tasks import search_article, delete_attached_picture, synchronous_username


@receiver(post_save, sender=Article)
def post_search_article(instance, created, **kwargs):
    if created:
        search_article.delay(
            instance.id, instance.content, instance.title, instance.tag, instance.publish_status, instance.user.username
        )


@receiver(pre_save, sender=Article)
def put_search_article(instance, update_fields, **kwargs):
    check = ['content', 'title', 'tag']
    if instance.id is not None and any([info in update_fields for info in check]):
        search_article.delay(
            instance.id, instance.content, instance.title, instance.tag, instance.publish_status, instance.user.username
        )


@receiver(pre_delete, sender=Article)
def delete_article_pictures(instance, **kwargs):
    delete_attached_picture.delay("article", instance.id)


@receiver(pre_delete, sender=Comment)
def delete_reply(instance, **kwargs):
    delete_reply.delay(instance.id)


@receiver(pre_save, sender=User)
def put_search_article(instance, update_fields, **kwargs):
    check = ['username']
    if instance.id is not None and any([info in update_fields for info in check]):
        old_instance = User.objects.filter(
            id=instance.id
        ).only('username').first()
        synchronous_username.delay(old_instance.username, instance.username)
