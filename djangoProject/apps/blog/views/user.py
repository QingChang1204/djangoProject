import uuid

from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
import re
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from blog.errcode import USER_INFO, EMAIL_FORMAT_ERROR, EXISTED_USER_NAME, TOKEN, PARAM_ERROR, SUCCESS, WEB_SOCKET_TOKEN
from blog.models import User, ReceiveMessage, WebSocketTicket
from blog.serializers import BlogUserSerializers
from blog.utils import custom_response, CustomAuth


class UserViewSets(GenericViewSet):
    queryset = User.objects.all()
    authentication_classes = [CustomAuth]
    permission_classes = [IsAuthenticated]
    serializer_class = BlogUserSerializers
    email_format = r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$'

    def list(self, request):
        """
        获得用户基本信息
        :param request:
        :return:
        """
        serializer = self.serializer_class(
            instance=request.user
        )
        USER_INFO['data'] = serializer.data
        return custom_response(USER_INFO, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[AllowAny | IsAuthenticated],
            authentication_classes=[CustomAuth])
    def sign_up(self, request):
        """
        用户注册接口
        :param request:
        :return:
        """
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
                return custom_response(EMAIL_FORMAT_ERROR, 200)
        except IntegrityError:
            return custom_response(EXISTED_USER_NAME, 200)
        except KeyError:
            return custom_response(PARAM_ERROR, 200)
        else:
            token = RefreshToken.for_user(blog_user)
            TOKEN['data'] = {
                'access_token': "Bearer " + str(token.access_token),
                'refresh': "Bearer " + str(token)
            }
            return custom_response(TOKEN, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[IsAuthenticated],
            authentication_classes=[CustomAuth])
    def update_info(self, request):
        """
        用户更新个人信息接口
        :param request:
        :return:
        """
        try:
            email = request.data.get('email', False)
            if email:
                if re.match(self.email_format, email):
                    blog_user = self.serializer_class(request.user, data=request.data, partial=True)
                    blog_user.is_valid(raise_exception=True)
                    blog_user.save()
                else:
                    return custom_response(EMAIL_FORMAT_ERROR, 200)
        except IntegrityError:
            return custom_response(EXISTED_USER_NAME, 200)
        else:
            return custom_response(SUCCESS, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[AllowAny | IsAuthenticated],
            authentication_classes=[CustomAuth])
    def log_in(self, request):
        """
        用户登录接口
        :param request:
        :return:
        """
        blog_user = authenticate(username=request.data['username'], password=request.data['password'])
        blog_user.last_login = timezone.now()
        blog_user.save(update_fields=['last_login', ])
        token = RefreshToken.for_user(
            blog_user
        )
        TOKEN['data'] = {
            'access_token': "Bearer " + str(token.access_token),
            'refresh': "Bearer " + str(token)
        }
        return custom_response(TOKEN, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[IsAuthenticated],
            authentication_classes=[CustomAuth])
    def message(self, request):
        try:
            content = request.data['content']
            user_id = int(request.data['user_id'])
        except (KeyError, ValueError, TypeError):
            return custom_response(PARAM_ERROR, 200)
        ReceiveMessage.objects.create(
            user_id=user_id,
            send_user_id=request.user.id,
            content=content
        )
        return custom_response(SUCCESS, 200)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[IsAuthenticated],
            authentication_classes=[CustomAuth])
    def get_ticket(self, request):
        user = request.user
        ticket, _ = WebSocketTicket.objects.get_or_create(
            user=user,
        )
        if _:
            ticket.ticket = uuid.uuid4()
            ticket.save(
                update_fields=[
                    'ticket'
                ]
            )
        WEB_SOCKET_TOKEN['data'] = {
            'ticket': str(ticket.ticket)
        }
        return custom_response(WEB_SOCKET_TOKEN, 200)
