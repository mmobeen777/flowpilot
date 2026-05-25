"""Common app models module."""
from django.db import models


class BaseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    objects = BaseManager()

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.is_active = False
        self.save()
