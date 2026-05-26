import re

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Create the configured PostgreSQL DB_SCHEMA if it does not exist."

    def handle(self, *args, **options):
        schema = settings.DATABASES["default"].get("OPTIONS", {}).get("options", "")
        match = re.search(r"search_path=([A-Za-z_][A-Za-z0-9_]*)", schema)
        if not match:
            self.stdout.write(self.style.WARNING("No DB_SCHEMA/search_path is configured."))
            return

        schema_name = match.group(1)
        if connection.vendor != "postgresql":
            self.stdout.write(self.style.WARNING("Schema creation is only needed for PostgreSQL."))
            return

        quoted_schema = connection.ops.quote_name(schema_name)
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {quoted_schema}")

        self.stdout.write(self.style.SUCCESS(f"Schema '{schema_name}' is ready."))
