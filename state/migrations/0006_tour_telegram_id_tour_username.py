# Generated by Django 5.1.1 on 2024-11-05 05:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('state', '0005_remove_tour_customer_tour_email_tour_full_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tour',
            name='telegram_id',
            field=models.CharField(default='123456789', max_length=255),
        ),
        migrations.AddField(
            model_name='tour',
            name='username',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]