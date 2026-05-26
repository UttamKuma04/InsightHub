from django.contrib import admin

from apps.core.models import Tenant, User


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "name", "tenant", "role", "is_active", "is_staff")
    list_filter = ("role", "tenant", "is_active", "is_staff")
    ordering = ("email",)
    search_fields = ("email", "name")
    readonly_fields = ("created_at", "last_login")
