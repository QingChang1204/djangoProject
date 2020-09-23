import json
from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
import re
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from blog.errcode import USER_INFO, EMAIL_FORMAT_ERROR, EXISTED_USER_NAME, TOKEN, PARAM_ERROR, SUCCESS, LOG_FAIL
from blog.models import User
from blog.serializers import BlogUserSerializers


class UserViewSets(GenericViewSet):
    queryset = User.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BlogUserSerializers
    email_format = r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$'

    def list(self, request):
        # 获得用户基本信息
        serializer = self.serializer_class(
            instance=request.user
        )
        USER_INFO['data'] = serializer.data
        return HttpResponse(json.dumps(USER_INFO, ensure_ascii=False), status=200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[AllowAny],
            authentication_classes=[])
    def sign_up(self, request):
        # 用户注册接口
        try:
            if re.match(self.email_format, request.data['email']):
                blog_user = self.serializer_class(
                    data=request.data
                )
                blog_user.is_valid(
                    raise_exception=True
                )
                blog_user = blog_user.save()
            else:
                return HttpResponse(json.dumps(EMAIL_FORMAT_ERROR, ensure_ascii=False), status=200)
        except IntegrityError:
            return HttpResponse(json.dumps(EXISTED_USER_NAME, ensure_ascii=False), status=200)
        except KeyError:
            return HttpResponse(json.dumps(PARAM_ERROR, ensure_ascii=False), status=200)
        else:
            token = RefreshToken.for_user(blog_user)
            TOKEN['data'] = {
                'access_token': "Bearer " + str(token.access_token),
                'refresh': "Bearer " + str(token)
            }
            return HttpResponse(json.dumps(TOKEN, ensure_ascii=False), status=200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[IsAuthenticated],
            authentication_classes=[JWTAuthentication])
    def update_info(self, request):
        # 用户更新个人信息
        try:
            if re.match(self.email_format, request.data['email']):
                blog_user = self.serializer_class(request.user, data=request.data, partial=True)
                blog_user.is_valid(raise_exception=True)
                blog_user.save()
            else:
                return HttpResponse(json.dumps(EMAIL_FORMAT_ERROR, ensure_ascii=False), status=200)
        except IntegrityError:
            return HttpResponse(json.dumps(EXISTED_USER_NAME, ensure_ascii=False), status=200)
        except KeyError:
            return HttpResponse(json.dumps(PARAM_ERROR, ensure_ascii=False), status=200)
        else:
            return HttpResponse(json.dumps(SUCCESS, ensure_ascii=False), status=200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[AllowAny],
            authentication_classes=[])
    def log_in(self, request):
        # 用户登录接口
        blog_user = authenticate(username=request.data['username'], password=request.data['password'])
        if blog_user is not None:
            blog_user.last_login = timezone.now()
            blog_user.save()
            token = RefreshToken.for_user(
                blog_user
            )
            TOKEN['data'] = {
                'access_token': "Bearer " + str(token.access_token),
                'refresh': "Bearer " + str(token)
            }
            return HttpResponse(json.dumps(TOKEN, ensure_ascii=False), status=200)
        else:
            return HttpResponse(json.dumps(LOG_FAIL), status=200)
