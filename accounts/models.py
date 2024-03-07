from django.db import models
from django.contrib.auth.models import User
from controls.models import UserGroup

class Profile(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    phone = models.CharField(max_length=200, blank=True, null=True)
    email = models.CharField(max_length=200, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    group = models.ManyToManyField(UserGroup)

    def __str__(self):
        return self.user.username