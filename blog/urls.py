from django.urls import path, include
from rest_framework import routers

app_name = 'blog'
router = routers.SimpleRouter()

urlpatterns = [
    path("", include(router.urls))
]