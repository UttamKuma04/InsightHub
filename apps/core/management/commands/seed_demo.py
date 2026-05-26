from django.core.management.base import BaseCommand

from apps.core.models import Tenant, User


class Command(BaseCommand):
    help = "Create a demo tenant and two users for local review."

    def handle(self, *args, **options):
        tenant, _ = Tenant.objects.get_or_create(name="InsightHub Demo")

        admin, _ = User.objects.get_or_create(
            email="admin@insighthub.local",
            defaults={
                "tenant": tenant,
                "name": "Admin User",
                "role": User.Role.ADMIN,
                "is_staff": True,
            },
        )
        admin.set_password("admin123")
        admin.save()

        analyst, _ = User.objects.get_or_create(
            email="analyst@insighthub.local",
            defaults={
                "tenant": tenant,
                "name": "Analyst User",
                "role": User.Role.ANALYST,
            },
        )
        analyst.set_password("analyst123")
        analyst.save()

        self.stdout.write(self.style.SUCCESS("Demo tenant and users are ready."))
