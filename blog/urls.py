from django.urls import path, include
from rest_framework import routers
from blog.views.article import ArticleViewSets
from blog.views.user import UserViewSets

app_name = 'blog'
router = routers.SimpleRouter()
router.register("user", UserViewSets)
router.register("article", ArticleViewSets)

urlpatterns = [
    path("", include(router.urls))
]
