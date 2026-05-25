from django.contrib.auth.models import BaseUserManager


class CustomManager(BaseUserManager):
    """Custom implementation of UserManager."""

    def _create_user(self,email, password, **extra_fields):
        """Create and save a user with given email and password."""

        if not email:
            raise ValueError("The given email must be set.")
        email = self.model.normalize_username(email)
        user = self.model(email=email, is_active=True, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email=None, password=None, **extra_fields):
        """Create User model with provided fields."""

        extra_fields.setdefault("is_superuser", False)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        """Create admin User model with provided fields."""

        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)
