# Generated by Django 2.2.25 on 2023-06-18 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('genplus', '0014_auto_20230531_1419'),
    ]

    operations = [
        migrations.AlterField(
            model_name='journalpost',
            name='journal_type',
            field=models.CharField(choices=[('TeacherFeedback', 'TeacherFeedback'), ('StudentReflection', 'StudentReflection'), ('ProblemEntry', 'ProblemEntry')], max_length=32),
        ),
    ]
