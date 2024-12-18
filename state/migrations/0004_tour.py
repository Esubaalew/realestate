# Generated by Django 5.1.1 on 2024-11-04 10:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('state', '0003_remove_property_video_customer_profile_token'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tour',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tour_date', models.DateField()),
                ('tour_time', models.TimeField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed')], default='pending', max_length=10)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='state.customer')),
                ('property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='state.property')),
            ],
        ),
    ]
