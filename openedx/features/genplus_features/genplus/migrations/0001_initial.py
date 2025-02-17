# Generated by Django 2.2.25 on 2022-11-29 18:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import openedx.features.genplus_features.genplus.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('actor_object_id', models.CharField(db_index=True, max_length=255)),
                ('type', models.CharField(choices=[('JournalEntryByStudent', 'JournalEntryByStudent'), ('JournalEntryByTeacher', 'JournalEntryByTeacher'), ('BadgeAward', 'BadgeAward'), ('LessonCompletion', 'LessonCompletion'), ('OnBoarded', 'OnBoarded')], max_length=128)),
                ('target_object_id', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('action_object_object_id', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('is_read', models.BooleanField(default=False)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Character',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('description', models.TextField()),
                ('profile_pic', models.ImageField(help_text='Upload the image which will be seen by student on their dashboard', upload_to='gen_plus_avatars')),
                ('standing', models.FileField(help_text='Provide standing position of character', upload_to='gen_plus_avatars', validators=[openedx.features.genplus_features.genplus.models.validate_file_extension])),
                ('dance1', models.FileField(help_text='Provide running position of character', upload_to='gen_plus_avatars', validators=[openedx.features.genplus_features.genplus.models.validate_file_extension])),
                ('dance2', models.FileField(help_text='Provide crouching position of character', upload_to='gen_plus_avatars', validators=[openedx.features.genplus_features.genplus.models.validate_file_extension])),
                ('dance3', models.FileField(help_text='Provide jumping position of character', upload_to='gen_plus_avatars', validators=[openedx.features.genplus_features.genplus.models.validate_file_extension])),
                ('dance4', models.FileField(help_text='Provide jumping position of character', upload_to='gen_plus_avatars', validators=[openedx.features.genplus_features.genplus.models.validate_file_extension])),
            ],
        ),
        migrations.CreateModel(
            name='Class',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('type', models.CharField(blank=True, choices=[('TeachingGroup', 'TeachingGroup'), ('RegistrationGroup', 'RegistrationGroup')], max_length=32, null=True)),
                ('group_id', models.CharField(max_length=128)),
                ('color', models.CharField(blank=True, choices=[('#E53935', '#E53935'), ('#AEEA00', '#AEEA00'), ('#EF6C00', '#EF6C00'), ('#304FFE', '#304FFE'), ('#0097A7', '#0097A7'), ('#1E88E5', '#1E88E5'), ('#388E3C', '#388E3C')], max_length=32, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='gen_plus_classes')),
                ('name', models.CharField(max_length=128)),
                ('is_visible', models.BooleanField(default=False, help_text='Manage Visibility to Genplus platform')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EmailRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('email_reference', models.BigIntegerField()),
                ('from_email', models.EmailField(max_length=254)),
                ('to_email', models.EmailField(max_length=254)),
                ('subject', models.CharField(choices=[('Missing Class', 'Missing Class')], max_length=128)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GenUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('role', models.CharField(blank=True, choices=[('Student', 'Student'), ('Faculty', 'Faculty'), ('Affiliate', 'Affiliate'), ('Employee', 'Employee'), ('TeachingStaff', 'TeachingStaff'), ('NonTeachingStaff', 'NonTeachingStaff')], max_length=32, null=True)),
                ('year_of_entry', models.CharField(blank=True, max_length=32, null=True)),
                ('registration_group', models.CharField(blank=True, max_length=32, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='School',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('guid', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=64)),
                ('external_id', models.CharField(max_length=32)),
                ('type', models.CharField(blank=True, choices=[('RmUnify', 'RmUnify'), ('Private', 'Private')], max_length=32, null=True)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='skill_images')),
            ],
        ),
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile_image', models.ImageField(blank=True, null=True, upload_to='gen_plus_teachers')),
            ],
        ),
        migrations.CreateModel(
            name='TeacherClass',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_favorite', models.BooleanField(default=False)),
                ('gen_class', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='genplus.Class')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='genplus.Teacher')),
            ],
        ),
        migrations.AddField(
            model_name='teacher',
            name='classes',
            field=models.ManyToManyField(related_name='teachers', through='genplus.TeacherClass', to='genplus.Class'),
        ),
        migrations.AddField(
            model_name='teacher',
            name='gen_user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='teacher', to='genplus.GenUser'),
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('onboarded', models.BooleanField(default=False)),
                ('active_class', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='genplus.Class')),
                ('character', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='genplus.Character')),
                ('gen_user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='student', to='genplus.GenUser')),
            ],
        ),
        migrations.CreateModel(
            name='JournalPost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('title', models.CharField(max_length=128)),
                ('description', models.TextField()),
                ('journal_type', models.CharField(choices=[('TeacherFeedback', 'TeacherFeedback'), ('StudentReflection', 'StudentReflection')], max_length=32)),
                ('skill', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='genplus.Skill')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='journal_posts', to='genplus.Student')),
                ('teacher', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='journal_feedbacks', to='genplus.Teacher')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='genuser',
            name='school',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='genplus.School'),
        ),
        migrations.AddField(
            model_name='genuser',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='gen_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='ClassStudents',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_visible', models.BooleanField(default=True)),
                ('gen_class', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='genplus.Class')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='genplus.Student')),
            ],
        ),
    ]
