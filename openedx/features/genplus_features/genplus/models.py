import os
import uuid
from django.core import signing
from django.conf import settings
from django.db import models
from django_extensions.db.models import TimeStampedModel
from jsonfield import JSONField
from .constants import GenUserRoles, ClassColors, JournalTypes, SchoolTypes, ClassTypes, ActivityTypes, EmailTypes, GenLogTypes
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

class LocalAuthorityDomain(TimeStampedModel):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name

class LocalAuthority(TimeStampedModel):
    name = models.CharField(max_length=64, unique=True)
    saml_configuration_slug = models.SlugField(null=True, blank=True, max_length=30,
                                               help_text='Slug of saml configuration i.e rmunify-dev, rmunify-stage')
    domains = models.ManyToManyField(LocalAuthorityDomain, blank=True, related_name='local_authorities')


    def __str__(self):
       return self.name


class School(TimeStampedModel):
    SCHOOL_CHOICES = SchoolTypes.__MODEL_CHOICES__
    local_authority = models.ForeignKey(LocalAuthority, on_delete=models.SET_NULL, null=True)
    guid = models.CharField(primary_key=True, max_length=128)
    name = models.CharField(max_length=64)
    external_id = models.CharField(max_length=32)
    cost_center = models.CharField(max_length=32,unique=True, default=None, null=True, blank=True,
                                    help_text='Need in the case of xporter schools.')
    type = models.CharField(blank=True, null=True, max_length=32, choices=SCHOOL_CHOICES)
    is_active = models.BooleanField(default=True,
                                    help_text='If De-selected the users related to this school cannot access the platform')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self._state.adding and self.type == SchoolTypes.PRIVATE and self.guid == '':
            self.guid = f'private-{str(uuid.uuid4())[0:10]}'
            self.external_id = f'private-{str(uuid.uuid4())[0:10]}'
        super(School, self).save(*args, **kwargs)
    class Meta:
        ordering = ['name', ]


class XporterDetail(TimeStampedModel):
    school = models.OneToOneField(School, on_delete=models.CASCADE, null=True, blank=True,
                                  related_name='xporter_detail')
    _secret = models.CharField(max_length=1024, null=True, blank=True)
    school_email = models.EmailField(null=True, blank=True)
    partner_id = models.CharField(max_length=1024, null=True, blank=True)
    _token = models.TextField(null=True, blank=True)
    token_expiry = models.DateTimeField(null=True, blank=True)
    last_exception_message = models.TextField(null=True, blank=True)

    # setter and getter of the encrypted fields
    @property
    def secret(self):
        # decrypt the encrypted value
        return signing.loads(self._secret)

    @secret.setter
    def secret(self, value):
        # Picks the `SECRET_KEY` provided in settings.py and encrypt it
        self._secret = signing.dumps(value)

    @property
    def token(self):
        return signing.loads(self._token)

    @token.setter
    def token(self, value):
        self._token = signing.dumps(value)


class Skill(models.Model):
    name = models.CharField(max_length=128, unique=True)
    image = models.ImageField(upload_to='skill_images', null=True, blank=True)

    def __str__(self):
        return self.name


# validate the file extensions for character model
def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.mp4', '.gif', '.jpg', '.jpeg', '.png']
    if not ext.lower() in valid_extensions:
        raise ValidationError(f'Unsupported file extension. supported files are {str(valid_extensions)}')


class Character(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField()
    skills = models.ManyToManyField(Skill, related_name='characters', blank=True)
    profile_pic = models.ImageField(upload_to='gen_plus_avatars',
                                    help_text='Upload the image which will be seen by student on their dashboard')
    standing = models.FileField(upload_to='gen_plus_avatars', validators=[validate_file_extension, ],
                                help_text='Provide standing position of character')
    dance1 = models.FileField(upload_to='gen_plus_avatars', validators=[validate_file_extension, ],
                              help_text='Provide running position of character')
    dance2 = models.FileField(upload_to='gen_plus_avatars', validators=[validate_file_extension, ],
                              help_text='Provide crouching position of character')
    dance3 = models.FileField(upload_to='gen_plus_avatars', validators=[validate_file_extension, ],
                              help_text='Provide jumping position of character')
    dance4 = models.FileField(upload_to='gen_plus_avatars', validators=[validate_file_extension, ],
                              help_text='Provide jumping position of character')

    def __str__(self):
        return self.name

    def get_state(self, progress):
        if 25 <= progress < 50:
            return self.dance2
        elif 50 <= progress < 75:
            return self.dance3
        elif 75 <= progress <= 100:
            return self.dance4
        return self.dance1


class GenUser(models.Model):
    ROLE_CHOICES = GenUserRoles.__MODEL_CHOICES__

    email = models.EmailField(unique=True, default=None, null=True, blank=True)
    identity_guid = models.CharField(null=True, max_length=1024)
    user = models.OneToOneField(USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='gen_user')
    role = models.CharField(blank=True, null=True, max_length=32, choices=ROLE_CHOICES)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True)
    year_of_entry = models.CharField(max_length=32, null=True, blank=True)
    registration_group = models.CharField(max_length=32, null=True, blank=True)
    has_password_changed = models.BooleanField(default=True,
                                               help_text='If selected, the user has changed their password. '
                                                         'De-select to force user to change password '
                                                         '(enforced immediately).')

    @property
    def is_student(self):
        return self.role == GenUserRoles.STUDENT

    @property
    def is_teacher(self):
        return self.role in GenUserRoles.TEACHING_ROLES

    @property
    def from_private_school(self):
        return self.school.type == SchoolTypes.PRIVATE

    @property
    def name(self):
        if self.school.type == SchoolTypes.XPORTER:
            first_name = getattr(self.user, 'first_name', '').strip()
            last_name = getattr(self.user, 'last_name', '').strip()
            if first_name or last_name:
                return f'{first_name} {last_name}'.strip()
        else:
            if self.user:
                profile_name = getattr(self.user.profile, 'name', '').strip()
                if profile_name:
                    return profile_name
            else:
                return self.email
            first_name = getattr(self.user, 'first_name', '').strip()
            last_name = getattr(self.user, 'last_name', '').strip()
            if first_name or last_name:
                return f'{first_name} {last_name}'.strip()

        return self.email

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if self._state.adding and self.school.type == SchoolTypes.PRIVATE:
            self.identity_guid = f'private-{str(uuid.uuid4())[0:10]}'
        super(GenUser, self).save(*args, **kwargs)


class Student(models.Model):
    gen_user = models.OneToOneField(GenUser, on_delete=models.CASCADE, related_name='student')
    character = models.ForeignKey(Character, on_delete=models.SET_NULL, null=True, blank=True)
    scn = models.CharField(unique=True, null=True, blank=True, max_length=255)
    active_class = models.ForeignKey('genplus.Class', on_delete=models.SET_NULL, null=True, blank=True)
    onboarded = models.BooleanField(default=False)

    class Meta:
        ordering = ('gen_user__user__first_name', )

    @property
    def user(self):
        return self.gen_user.user

    @property
    def has_access_to_lessons(self):
        return self.classes.count() > 0

    def __str__(self):
        return self.gen_user.email or ''


class ClassManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_visible=True)


class Class(TimeStampedModel):
    COLOR_CHOICES = ClassColors.__MODEL_CHOICES__
    CLASS_CHOICES = ClassTypes.__MODEL_CHOICES__
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='classes')
    type = models.CharField(blank=True, null=True, max_length=32, choices=CLASS_CHOICES)
    group_id = models.CharField(max_length=128)
    color = models.CharField(blank=True, null=True, max_length=32, choices=COLOR_CHOICES)
    image = models.ImageField(upload_to='gen_plus_classes', null=True, blank=True)
    name = models.CharField(max_length=128)
    is_visible = models.BooleanField(default=False, help_text='Manage Visibility to Genplus platform')
    students = models.ManyToManyField(Student, blank=True, through="genplus.ClassStudents", related_name='classes')
    program = models.ForeignKey('genplus_learning.Program', on_delete=models.CASCADE, null=True, blank=True,
                                related_name="classes")
    last_synced = models.DateTimeField(null=True, blank=True)
    objects = models.Manager()
    visible_objects = ClassManager()

    def __str__(self):
        return self.name


class Teacher(models.Model):
    gen_user = models.OneToOneField(GenUser, on_delete=models.CASCADE, related_name='teacher')
    profile_image = models.ImageField(upload_to='gen_plus_teachers', null=True, blank=True)
    favorite_classes = models.ManyToManyField(Class, related_name='teachers', blank=True)

    @property
    def user(self):
        return self.gen_user.user

    def __str__(self):
        return self.gen_user.email


class ClassStudents(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    gen_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    is_visible = models.BooleanField(default=True)


class JournalPost(TimeStampedModel):
    JOURNAL_TYPE_CHOICES = JournalTypes.__MODEL_CHOICES__
    class Meta:
        unique_together = ("uuid", "student",)

    uuid = models.CharField(max_length=64, default=uuid.uuid4, editable=False, null=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="journal_posts")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, related_name="journal_feedbacks")
    title = models.CharField(max_length=128)
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    journal_type = models.CharField(max_length=32, choices=JOURNAL_TYPE_CHOICES)
    is_editable = models.BooleanField(default=True)


class ActivityManager(models.Manager):
    def student_activities(self, student_id=None):
        return super().get_queryset().filter(target_content_type__model='student',
                                             target_object_id=student_id).order_by('-created')


class Activity(TimeStampedModel):
    ACTIVITY_TYPE = ActivityTypes.__MODEL_CHOICES__

    # Actor: The object that performed the activity.
    actor_content_type = models.ForeignKey(
        ContentType, related_name='actor', blank=True, null=True,
        on_delete=models.CASCADE, db_index=True
    )
    actor_object_id = models.CharField(max_length=255, db_index=True)
    actor = GenericForeignKey('actor_content_type', 'actor_object_id')

    # Type: the type of activity perform
    type = models.CharField(max_length=128, choices=ACTIVITY_TYPE)

    # Target: The object to which the activity was performed
    target_content_type = models.ForeignKey(
        ContentType, blank=True, null=True,
        related_name='target',
        on_delete=models.CASCADE, db_index=True
    )
    target_object_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    target = GenericForeignKey(
        'target_content_type',
        'target_object_id'
    )
    # Action : The object linked to the action itself
    action_object_content_type = models.ForeignKey(
        ContentType, blank=True, null=True,
        related_name='action_object',
        on_delete=models.CASCADE, db_index=True
    )
    action_object_object_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    action_object = GenericForeignKey(
        'action_object_content_type',
        'action_object_object_id'
    )
    is_read = models.BooleanField(default=False)
    objects = ActivityManager()


class EmailRecord(TimeStampedModel):
    EMAIL_TYPE_CHOICES = EmailTypes.__MODEL_CHOICES__
    email_reference = models.BigIntegerField()
    from_email = models.EmailField()
    to_email = models.EmailField()
    subject = models.CharField(max_length=128, choices=EMAIL_TYPE_CHOICES)

    def save(self, *args, **kwargs):
        record = EmailRecord.objects.filter(subject=self.subject).order_by('-email_reference').first()
        if record:
            self.email_reference = record.email_reference + 1
        else:
            self.email_reference = 1

        super(EmailRecord, self).save(*args, **kwargs)


class GenLog(TimeStampedModel):
    GEN_LOG_TYPE_CHOICES = GenLogTypes.__MODEL_CHOICES__
    gen_log_type = models.CharField(max_length=128, choices=GEN_LOG_TYPE_CHOICES)
    description = models.TextField(null=True)
    metadata = JSONField(
        null=True,
        blank=True,
        help_text='store data according to the log type'
    )

    def __str__(self):
        return self.description

    @classmethod
    def create_student_log(cls, gen_class, student_ids, log_type):
        remove_student_logs = []
        for student in Student.objects.filter(id__in=student_ids):
            remove_student_logs.append(
                cls(
                    gen_log_type=log_type,
                    description=f'{student.gen_user.email} {log_type} {gen_class.name}',
                    metadata={
                        'email': student.gen_user.email,
                        'identity_guid': student.gen_user.identity_guid,
                        'user_id': student.gen_user.user.id if student.gen_user.user is not None else None,
                        'class_id': gen_class.id,
                        'class_name': gen_class.name,
                        'school': gen_class.school.name,
                    }
                )
            )
        cls.objects.bulk_create(remove_student_logs)

    @classmethod
    def create_remove_user_log(cls, user_guid, details=None):
        cls.objects.create(
            gen_log_type=GenLogTypes.RM_UNIFY_PROVISION_UPDATE_USER_DELETE,
            description=f'user with guid {user_guid} removed from the system',
            metadata=details,
        )

    @classmethod
    def create_more_than_one_school_log(cls, email, school, class_name):
        cls.objects.create(
            gen_log_type=GenLogTypes.STUDENT_PART_OF_MORE_THAN_ONE_SCHOOL,
            description=f'user with {email} is part of more than one school',
            metadata={
                'school': school,
                'class': class_name,
                'email': email
            },
        )

    @classmethod
    def program_enrollment_log(cls, email, details=None):
        cls.objects.create(
            gen_log_type=GenLogTypes.PROGRAM_ENROLLMENTS_REMOVE,
            description=f'Program Enrollment delete for user {email}',
            metadata=details
        )

    @classmethod
    def registration_failed(cls, email, details=None):
        cls.objects.create(
            gen_log_type=GenLogTypes.REGISTRATION_FAILED,
            description=f'Registration failed for {email}',
            metadata=details
        )


class GenError(models.Model):
    ROLE_CHOICES = GenUserRoles.__MODEL_CHOICES__
    email = models.EmailField()
    name = models.CharField(max_length=64)
    role = models.CharField(blank=True, null=True, max_length=32, choices=ROLE_CHOICES)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True)
    gen_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True)
    error_code = models.IntegerField(null=True, blank=True)
    browser = models.CharField(max_length=32, null=True, blank=True)
    os = models.CharField(max_length=32, null=True, blank=True)
    device = models.CharField(max_length=32, null=True, blank=True)
