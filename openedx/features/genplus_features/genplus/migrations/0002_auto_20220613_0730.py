# Generated by Django 2.2.25 on 2022-06-13 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('genplus', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='genuser',
            name='role',
            field=models.CharField(blank=True, choices=[('Student', 'Student'), ('Faculty', 'Faculty'), ('Affiliate', 'Affiliate'), ('Employee', 'Employee'), ('TeachingStaff', 'TeachingStaff'), ('NonTeachingStaff', 'NonTeachingStaff')], max_length=32, null=True),
        ),
    ]
