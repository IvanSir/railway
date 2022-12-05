# Generated by Django 4.1.3 on 2022-11-29 22:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tickets', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='carriage',
            name='carriage_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tickets.carriagetype'),
        ),
        migrations.AddField(
            model_name='carriage',
            name='route',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='carriages', to='tickets.route'),
        ),
        migrations.AddField(
            model_name='arrivalpoint',
            name='arrival_city',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='arrivals', to='tickets.city'),
        ),
    ]
