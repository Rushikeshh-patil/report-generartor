# Generated by Django 5.0.14 on 2025-07-24 01:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0003_project_project_manager'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='due_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
