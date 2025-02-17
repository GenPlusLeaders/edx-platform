# Generated by Django 2.2.25 on 2023-03-01 03:47

from django.db import migrations, models
import django_extensions.db.fields
import jsonfield.encoder
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('genplus', '0006_genuser_has_password_changed'),
    ]

    operations = [
        migrations.CreateModel(
            name='GenLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('gen_log_type', models.CharField(choices=[('RMUnify provision update user deleted', 'RMUnify provision update user deleted'), ('Student removed from class', 'Student removed from class')], max_length=128)),
                ('description', models.TextField(null=True)),
                ('metadata', jsonfield.fields.JSONField(blank=True, dump_kwargs={'cls': jsonfield.encoder.JSONEncoder, 'separators': (',', ':')}, help_text='store data according to the log type', load_kwargs={}, null=True)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
    ]
