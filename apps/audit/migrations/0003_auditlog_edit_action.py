from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0002_auditlog_delete_action"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="action",
            field=models.CharField(
                choices=[
                    ("CREATE", "Create"),
                    ("EDIT", "Edit"),
                    ("APPROVE", "Approve"),
                    ("REJECT", "Reject"),
                    ("DELETE", "Delete"),
                ],
                max_length=20,
            ),
        ),
    ]
