from django.urls import path, include
from rest_framework import routers

from blog.views.user import UserViewSets

app_name = 'blog'
router = routers.SimpleRouter()
router.register("user", UserViewSets)

urlpatterns = [
    path("", include(router.urls))
]