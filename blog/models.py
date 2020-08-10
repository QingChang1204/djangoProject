from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.

class BlogUser(AbstractUser):
    display_account = models.CharField(max_length=12, null=False)

    def __str__(self):
        return self.username

