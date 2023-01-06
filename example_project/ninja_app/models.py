from django.conf import settings
from django.db import models


class NoteNinjaApp(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    heading = models.CharField(max_length=512)
    content = models.TextField()


class TagNinjaApp(models.Model):
    value = models.CharField(max_length=512)
    note = models.ForeignKey(NoteNinjaApp, on_delete=models.CASCADE)
