# Generated by Django 3.0.5 on 2022-12-12 10:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='discount',
            name='usage_amount',
            field=models.IntegerField(default=0),
        ),
    ]
