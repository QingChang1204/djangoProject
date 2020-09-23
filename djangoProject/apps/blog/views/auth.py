from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from blog.models import User


class CustomBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        try:
            user = User.objects.get(
                Q(username=username) |
                Q(phone=username)
            )
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
