from django.db import models

class DevTool(models.Model):
    name = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        verbose_name = "Dev Tool"
        verbose_name_plural = "Dev Tools"