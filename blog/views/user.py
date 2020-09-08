from django.db import IntegrityError
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import re
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
import blog.errcode as errcode
from blog.models import BlogUser
from blog.serializers import BlogUserSerializers


class UserViewSets(viewsets.GenericViewSet):
    queryset = BlogUser.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BlogUserSerializers
    email_format = r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$'

    @staticmethod
    def list(request):
        # 获得用户基本信息
        user = request.user
        errcode.USER_INFO['data'] = {
            "icon": user.icon,
            "username": user.username,
            "description": user.description,
            "email": user.email,
            "display_account": user.display_account,
            "phone": user.phone
        }
        return Response(errcode.USER_INFO, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[AllowAny],
            authentication_classes=[])
    def sign_up(self, request):
        # 用户注册接口
        try:
            if re.match(self.email_format, request.data['email']):
                blog_user = self.get_serializer(data=request.data)
                blog_user.is_valid(raise_exception=True)
                blog_user = blog_user.save()
            else:
                return Response(errcode.EMAIL_FORMAT_ERROR, 200)
        except IntegrityError:
            return Response(errcode.EXISTED_USER_NAME, 200)
        else:
            token = RefreshToken.for_user(blog_user)
            errcode.TOKEN['data'] = {
                'access_token': "Bearer " + str(token.access_token),
                'refresh': "Bearer " + str(token)
            }
            return Response(errcode.TOKEN, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[IsAuthenticated],
            authentication_classes=[JWTAuthentication])
    def update_info(self, request):
        # 用户更新个人信息
        try:
            request.data['display_account']
        except KeyError:
            return Response(errcode.PARAM_ERROR, 200)
        try:
            if re.match(self.email_format, request.data['email']):
                blog_user = self.get_serializer(request.user, data=request.data)
                blog_user.is_valid(raise_exception=True)
                blog_user.save()
            else:
                return Response(errcode.EMAIL_FORMAT_ERROR, 200)
        except IntegrityError:
            return Response(errcode.EXISTED_USER_NAME, 200)
        else:
            return Response(errcode.SUCCESS, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[AllowAny],
            authentication_classes=[])
    def log_in(self, request):
        # 用户登录接口
        try:
            blog_user = self.queryset.list()
            if blog_user.check_password(request.data['password']):
                token = RefreshToken.for_user(
                    self.queryset.list()
                )
                errcode.TOKEN['data'] = {
                    'access_token': "Bearer " + str(token.access_token),
                    'refresh': "Bearer " + str(token)
                }
                return Response(errcode.TOKEN, 200)
            else:
                return Response(errcode.PARAM_ERROR, 200)
        except (KeyError, BlogUser.DoesNotExist):
            return Response(errcode.PARAM_ERROR, 200)
