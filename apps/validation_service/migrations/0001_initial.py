from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("ingestion", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ValidationIssue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("record_type", models.CharField(max_length=30)),
                ("record_id", models.PositiveBigIntegerField()),
                ("severity", models.CharField(choices=[("INFO", "Info"), ("WARNING", "Warning"), ("ERROR", "Error")], max_length=20)),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "validation_issues", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="validationissue",
            index=models.Index(fields=["record_type", "record_id"], name="validation_record_idx"),
        ),
        migrations.AddIndex(
            model_name="validationissue",
            index=models.Index(fields=["severity"], name="validation_severity_idx"),
        ),
    ]
