from django.db import models

class InvitationKey(models.Model):
    key = models.CharField('key', max_length=40, unique=True)
    used = models.BooleanField()