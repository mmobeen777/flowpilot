from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from .manager import CustomManager
from ..utils.Models import BaseModel
from ..utils.Fields import CharIDField


class Organization(BaseModel):
    """Class for Organization model."""

    id = CharIDField(primary_key=True, prefix='org_')
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)

    class Meta:
        """Metaclass for Organization model."""

        db_table = 'organization'
        ordering = ['name']

    def __str__(self):
        """Return string representation of Organization model."""
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    """This class represents the User model"""

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    id = CharIDField(primary_key=True, prefix="usr_")

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)

    password = models.CharField(max_length=255)

    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="members")

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)

    is_superuser = models.BooleanField(
        default=False,
        help_text='Designates whether the user can log into this admin site.',
    )

    last_login = models.DateTimeField(null=True)
    last_logout = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    REQUIRED_FIELDS = ('role', 'first_name', 'last_name')
    USERNAME_FIELD = 'email'

    objects = CustomManager()

    class Meta:
        """Class for User model."""

        db_table = 'users'
        ordering = ['email']

    def __str__(self):
        """Return string representation of User model."""
        return self.email

    @property
    def is_owner(self):
        """Return True if the user has the OWNER role, otherwise False."""
        return self.role == self.Role.OWNER

    @property
    def is_admin(self):
        """Return True if the user has the ADMIN role, otherwise False."""
        return self.role == self.Role.ADMIN

