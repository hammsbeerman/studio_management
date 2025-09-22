from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from controls.models import UserGroup

class Profile(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    phone = models.CharField(max_length=200, blank=True, null=True)
    email = models.CharField(max_length=200, blank=True, null=True)
    primary_company = models.CharField(
        "Internal Company",
        choices=[("LK Design", "LK Design"), ("Krueger Printing", "Krueger Printing")],
        max_length=100,
        blank=False,
        null=False,
    )
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    group = models.ManyToManyField(UserGroup)

    def __str__(self):
        # guard against null user, just in case
        return self.user.username if self.user_id else "Profile"