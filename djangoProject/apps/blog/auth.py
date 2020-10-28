from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from rest_framework.exceptions import APIException
from blog.models import User


class AuthenticationFailed(APIException):
    status_code = 401
    default_detail = 'Incorrect authentication credentials.'
    default_code = 'authentication_failed'


class CustomBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None or not username or not password:
            raise AuthenticationFailed(
                "用户名或者密码不可为空。"
            )

        user = User.objects.filter(
            Q(username=username) |
            Q(phone=username)
        ).only(
            'is_active', 'is_staff', 'id', 'is_superuser', 'username', 'password'
        ).first()
        if user is None:
            raise AuthenticationFailed(
                "账号不存在,请核对账号后重新输入。"
            )
        if user.check_password(password):
            return user
        else:
            raise AuthenticationFailed(
                "密码不正确,请重新输入。"
            )
