# Generated by Django 2.2.25 on 2023-02-02 09:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('genplus', '0005_genuser_identity_guid'),
    ]

    operations = [
        migrations.AddField(
            model_name='genuser',
            name='has_password_changed',
            field=models.BooleanField(default=True, help_text='Mark this as false to force user to change it password.'),
        ),
    ]
