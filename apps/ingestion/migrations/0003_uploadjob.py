import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ingestion", "0002_electricityrecord_account_no_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UploadJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_type", models.CharField(choices=[("SAP", "SAP"), ("UTILITY", "Utility"), ("TRAVEL", "Travel")], max_length=20)),
                ("file", models.FileField(upload_to="uploads/%Y/%m/%d/")),
                ("original_filename", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("QUEUED", "Queued"), ("PROCESSING", "Processing"), ("COMPLETED", "Completed"), ("FAILED", "Failed")], default="QUEUED", max_length=20)),
                ("total_records", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="upload_jobs", to="core.tenant")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="upload_jobs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "upload_jobs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="uploadjob",
            index=models.Index(fields=["tenant", "status"], name="upload_job_tenant_status_idx"),
        ),
    ]
