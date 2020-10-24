from django.urls import path, include
from rest_framework import routers
from blog.views.article import ArticleViewSets, CommentViewSets
from blog.views.user import UserViewSets

app_name = 'blog'
router = routers.SimpleRouter()
router.register("user", UserViewSets)
router.register("article", ArticleViewSets)
router.register("comment", CommentViewSets)

urlpatterns = router.urls
