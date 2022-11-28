# Generated by Django 2.2.25 on 2022-10-03 11:52

import django.db.models.deletion
import django_extensions.db.fields
import tinymce.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('genplus', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('title', models.CharField(max_length=1024)),
                ('cover', models.ImageField(help_text='Upload the cover for the article', upload_to='article_covers')),
                ('summary', tinymce.models.HTMLField()),
                ('content', tinymce.models.HTMLField()),
                ('author', models.CharField(help_text='Add name of the author', max_length=1024)),
                ('time', models.PositiveIntegerField(default=0, help_text='Time required to read/watch/listen the article')),
                ('is_draft', models.BooleanField(default=False)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Gtcs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=1024)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MediaType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Reflection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('title', models.TextField()),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reflections', to='genplus_teach.Article')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FavoriteArticle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='genplus_teach.Article')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorite_articles', to='genplus.Teacher')),
            ],
        ),
        migrations.CreateModel(
            name='ArticleViewLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('count', models.PositiveIntegerField(default=0, help_text='Views count on each article.')),
                ('engagement', models.PositiveIntegerField(default=0, help_text='Length of engagement in seconds')),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='view_logs', to='genplus_teach.Article')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='genplus.Teacher')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='article',
            name='gtcs',
            field=models.ManyToManyField(related_name='articles', to='genplus_teach.Gtcs'),
        ),
        migrations.AddField(
            model_name='article',
            name='media_types',
            field=models.ManyToManyField(related_name='articles', to='genplus_teach.MediaType'),
        ),
        migrations.AddField(
            model_name='article',
            name='skills',
            field=models.ManyToManyField(related_name='articles', to='genplus.Skill'),
        ),
        migrations.CreateModel(
            name='ReflectionAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('answer', models.TextField()),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reflections_answers', to='genplus_teach.Article')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='genplus.Teacher')),
            ],
            options={
                'unique_together': {('article', 'teacher')},
            },
        ),
        migrations.CreateModel(
            name='ArticleRating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('rating', models.PositiveIntegerField(default=0)),
                ('comment', models.TextField()),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='genplus_teach.Article')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='genplus.Teacher')),
            ],
            options={
                'unique_together': {('teacher', 'article')},
            },
        ),
    ]
