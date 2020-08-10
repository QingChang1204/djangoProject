from rest_framework import viewsets
from rest_framework.response import Response
import blog.errcode as ec

from blog.models import BlogUser


class UserViewSets(viewsets.ModelViewSet):
    queryset = BlogUser.objects.all()
    authentication_classes = []
    permission_classes = []
    serializer_class = []

    def list(self, request, *args, **kwargs):
        return Response(ec.SUCCESS, 200)
