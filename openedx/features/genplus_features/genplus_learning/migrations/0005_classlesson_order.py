# Generated by Django 2.2.25 on 2022-08-25 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('genplus_learning', '0004_classunit_course_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='classlesson',
            name='order',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
