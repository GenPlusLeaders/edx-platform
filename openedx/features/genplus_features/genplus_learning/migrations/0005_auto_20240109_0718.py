# Generated by Django 2.2.25 on 2024-01-09 07:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('genplus_learning', '0004_auto_20230904_1217'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalprogram',
            name='sort_order',
            field=models.IntegerField(default=None),
        ),
        migrations.AddField(
            model_name='program',
            name='sort_order',
            field=models.IntegerField(default=None),
        ),
    ]
