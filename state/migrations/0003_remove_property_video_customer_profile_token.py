# Generated by Django 5.1.1 on 2024-11-01 06:38

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('state', '0002_alter_customer_email'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='property',
            name='video',
        ),
        migrations.AddField(
            model_name='customer',
            name='profile_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]