# Generated by Django 2.2.25 on 2023-07-17 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('genplus_assessments', '0004_auto_20230623_0915'),
    ]

    operations = [
        migrations.AlterField(
            model_name='skillassessmentresponse',
            name='skill_assessment_type',
            field=models.CharField(choices=[('likert', 'likert')], max_length=32, null=True),
        ),
    ]
