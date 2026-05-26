from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DataSource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_type", models.CharField(choices=[("SAP", "SAP"), ("UTILITY", "Utility"), ("TRAVEL", "Travel")], max_length=20)),
                ("filename", models.CharField(max_length=255)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="data_sources", to="core.tenant")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="uploads", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "data_sources", "ordering": ["-uploaded_at"]},
        ),
        migrations.CreateModel(
            name="FuelRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(blank=True, null=True)),
                ("plant_code", models.CharField(blank=True, max_length=100)),
                ("fuel_type", models.CharField(blank=True, max_length=100)),
                ("quantity", models.DecimalField(decimal_places=3, max_digits=14)),
                ("unit", models.CharField(blank=True, max_length=20)),
                ("normalized_quantity", models.DecimalField(decimal_places=3, max_digits=14)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("APPROVED", "Approved"), ("REJECTED", "Rejected")], default="PENDING", max_length=20)),
                ("locked", models.BooleanField(default=False)),
                ("datasource", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fuel_records", to="ingestion.datasource")),
            ],
            options={"db_table": "fuel_records", "ordering": ["-id"]},
        ),
        migrations.CreateModel(
            name="ElectricityRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("meter_id", models.CharField(blank=True, max_length=100)),
                ("billing_start", models.DateField(blank=True, null=True)),
                ("billing_end", models.DateField(blank=True, null=True)),
                ("kwh", models.DecimalField(decimal_places=3, max_digits=14)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("APPROVED", "Approved"), ("REJECTED", "Rejected")], default="PENDING", max_length=20)),
                ("locked", models.BooleanField(default=False)),
                ("datasource", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="electricity_records", to="ingestion.datasource")),
            ],
            options={"db_table": "electricity_records", "ordering": ["-id"]},
        ),
        migrations.CreateModel(
            name="TravelRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("trip_type", models.CharField(blank=True, max_length=100)),
                ("origin", models.CharField(blank=True, max_length=100)),
                ("destination", models.CharField(blank=True, max_length=100)),
                ("distance_km", models.DecimalField(decimal_places=3, max_digits=14)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("APPROVED", "Approved"), ("REJECTED", "Rejected")], default="PENDING", max_length=20)),
                ("locked", models.BooleanField(default=False)),
                ("datasource", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="travel_records", to="ingestion.datasource")),
            ],
            options={"db_table": "travel_records", "ordering": ["-id"]},
        ),
        migrations.AddIndex(
            model_name="datasource",
            index=models.Index(fields=["tenant", "source_type"], name="data_source_tenant_source_idx"),
        ),
        migrations.AddIndex(
            model_name="fuelrecord",
            index=models.Index(fields=["status", "locked"], name="fuel_record_status_locked_idx"),
        ),
        migrations.AddIndex(
            model_name="electricityrecord",
            index=models.Index(fields=["status", "locked"], name="electricity_status_locked_idx"),
        ),
        migrations.AddIndex(
            model_name="travelrecord",
            index=models.Index(fields=["status", "locked"], name="travel_status_locked_idx"),
        ),
    ]
