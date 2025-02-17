# Generated by Django 2.2.25 on 2022-11-29 18:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('genplus_learning', '0001_initial'),
        ('genplus', '0001_initial'),
        ('genplus_assessments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userresponse',
            name='program',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='genplus_learning.Program'),
        ),
        migrations.AddField(
            model_name='userresponse',
            name='skill',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='genplus.Skill'),
        ),
        migrations.AddField(
            model_name='userresponse',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='userrating',
            name='gen_class',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='genplus.Class'),
        ),
        migrations.AddField(
            model_name='userrating',
            name='program',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='genplus_learning.Program'),
        ),
        migrations.AddField(
            model_name='userrating',
            name='skill',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='genplus.Skill'),
        ),
        migrations.AddField(
            model_name='userrating',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
