from django.contrib import admin

from .models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("name", "prefix", "organization", "is_active", "last_used_at", "expires_at", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "prefix", "organization__name")
    readonly_fields = ("prefix", "hashed_key", "last_used_at", "created_at", "updated_at")
    fields = ("name", "organization", "created_by", "prefix", "hashed_key", "allowed_ips",
              "expires_at", "last_used_at", "is_active", "created_at", "updated_at")
