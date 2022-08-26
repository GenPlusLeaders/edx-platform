from django.db import models

from openedx.features.genplus_features.genplus.models import Skill


class BoosterBadge(models.Model):
    slug = models.SlugField(max_length=255, validators=[validate_lowercase])
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='booster_badge_classes', validators=[validate_badge_image])

    def get_for_user(self, user):
        """
        Get the assertion for this badge class for this user, if it has been awarded.
        """
        return self.badgeassertion_set.filter(user=user)

    def award(self, user, evidence_url=None):
        """
        Contacts the backend to have a badge assertion created for this badge class for this user.
        """
        return self.backend.award(self, user, evidence_url=evidence_url)  # lint-amnesty, pylint: disable=no-member

    def save(self, **kwargs):  # lint-amnesty, pylint: disable=arguments-differ
        """
        Slugs must always be lowercase.
        """
        self.slug = self.slug and self.slug.lower()
        self.issuing_component = self.issuing_component and self.issuing_component.lower()
        super().save(**kwargs)

    class Meta:
        unique_together = (('slug', 'issuing_component', 'course_id'),)
        verbose_name_plural = "Badge Classes"


class BoosterBadgeAward(TimeStampedModel):
    """
    Tracks badges on our side of the badge baking transaction

    .. no_pii:
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge_class = models.ForeignKey(BadgeClass, on_delete=models.CASCADE)
    data = JSONField()
    backend = models.CharField(max_length=50)
    image_url = models.URLField()
    assertion_url = models.URLField()

    def __str__(self):  # lint-amnesty, pylint: disable=invalid-str-returned
        return HTML("<{username} Badge Assertion for {slug} for {issuing_component}").format(
            username=HTML(self.user.username),
            slug=HTML(self.badge_class.slug),
            issuing_component=HTML(self.badge_class.issuing_component),
        )

    @classmethod
    def assertions_for_user(cls, user, course_id=None):
        """
        Get all assertions for a user, optionally constrained to a course.
        """
        if course_id:
            return cls.objects.filter(user=user, badge_class__course_id=course_id)
        return cls.objects.filter(user=user)

    class Meta:
        app_label = "badges"


# Abstract model doesn't index this, so we have to.
BadgeAssertion._meta.get_field('created').db_index = True


class CourseCompleteImageConfiguration(models.Model):
    """
    Contains the icon configuration for badges for a specific course mode.

    .. no_pii:
    """
    mode = models.CharField(
        max_length=125,
        help_text=_('The course mode for this badge image. For example, "verified" or "honor".'),
        unique=True,
    )
    icon = models.ImageField(
        # Actual max is 256KB, but need overhead for badge baking. This should be more than enough.
        help_text=_(
            "Badge images must be square PNG files. The file size should be under 250KB."
        ),
        upload_to='course_complete_badges',
        validators=[validate_badge_image]
    )
    default = models.BooleanField(
        help_text=_(
            "Set this value to True if you want this image to be the default image for any course modes "
            "that do not have a specified badge image. You can have only one default image."
        ),
        default=False,
    )

    def __str__(self):  # lint-amnesty, pylint: disable=invalid-str-returned
        return HTML("<CourseCompleteImageConfiguration for '{mode}'{default}>").format(
            mode=HTML(self.mode),
            default=HTML(" (default)") if self.default else HTML('')
        )

    def clean(self):
        """
        Make sure there's not more than one default.
        """
        if self.default and CourseCompleteImageConfiguration.objects.filter(default=True).exclude(id=self.id):
            raise ValidationError(_("There can be only one default image."))

    @classmethod
    def image_for_mode(cls, mode):
        """
        Get the image for a particular mode.
        """
        try:
            return cls.objects.get(mode=mode).icon
        except cls.DoesNotExist:
            # Fall back to default, if there is one.
            return cls.objects.get(default=True).icon

    class Meta:
        app_label = "badges"
