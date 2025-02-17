# Generated by Django 2.2.25 on 2023-10-10 07:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('genplus', '0020_school_cost_center'),
    ]

    operations = [
        migrations.AlterField(
            model_name='genuser',
            name='role',
            field=models.CharField(blank=True, choices=[('Student', 'Student'), ('Faculty', 'Faculty'), ('Affiliate', 'Affiliate'), ('Employee', 'Employee'), ('TeachingStaff', 'TeachingStaff'), ('NonTeachingStaff', 'NonTeachingStaff'), ('staff', 'staff')], max_length=32, null=True),
        ),
        migrations.AlterField(
            model_name='school',
            name='cost_center',
            field=models.CharField(blank=True, default=None, help_text='Need in the case of xporter schools.', max_length=32, null=True, unique=True),
        ),
    ]
