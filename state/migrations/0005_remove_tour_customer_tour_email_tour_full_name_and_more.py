# Generated by Django 5.1.1 on 2024-11-04 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('state', '0004_tour'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tour',
            name='customer',
        ),
        migrations.AddField(
            model_name='tour',
            name='email',
            field=models.EmailField(default='mail@state.et', max_length=254),
        ),
        migrations.AddField(
            model_name='tour',
            name='full_name',
            field=models.CharField(default='John Doe', max_length=255),
        ),
        migrations.AddField(
            model_name='tour',
            name='phone_number',
            field=models.CharField(default='+251911223344', max_length=15),
        ),
        migrations.AlterField(
            model_name='tour',
            name='tour_date',
            field=models.CharField(choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday')], default='Monday', max_length=9),
        ),
        migrations.AlterField(
            model_name='tour',
            name='tour_time',
            field=models.IntegerField(choices=[(1, '1 AM'), (2, '2 AM'), (3, '3 AM'), (4, '4 AM'), (5, '5 AM'), (6, '6 AM'), (7, '7 AM'), (8, '8 AM'), (9, '9 AM'), (10, '10 AM'), (11, '11 AM'), (12, '12 PM')], default=1),
        ),
    ]