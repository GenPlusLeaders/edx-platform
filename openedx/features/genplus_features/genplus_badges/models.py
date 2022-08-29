from django.db import models

from openedx.features.genplus_features.genplus.models import Skill

def validate_badge_image(image):
    """
    Validates that a particular image is small enough to be a badge and square.
    """
    if image.width != image.height:
        raise ValidationError(_("The badge image must be square."))
    if not image.size < (250 * 1024):
        raise ValidationError(_("The badge image file size must be less than 250KB."))


def validate_lowercase(string):
    """
    Validates that a string is lowercase.
    """
    if not string.islower():
        raise ValidationError(_("This value must be all lowercase."))


class BoosterBadge(models.Model):
    slug = models.SlugField(max_length=255, unique=True, validators=[validate_lowercase])
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='booster_badge_classes', validators=[validate_badge_image])

    def get_for_user(self, user):
        return self.boosterbadgeaward_set.filter(user=user).first()

    def save(self, **kwargs):  # lint-amnesty, pylint: disable=arguments-differ
        self.slug = self.slug and self.slug.lower()
        super().save(**kwargs)

    class Meta:
        verbose_name_plural = "Booster Badges"


class BoosterBadgeAward(TimeStampedModel):
    class Meta:
        unique_together = ('user', 'badge',)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(BoosterBadge, on_delete=models.CASCADE)
    awarded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback = models.TextField()
    image_url = models.URLField()

    @classmethod
    def awards_for_user(cls, user):
        return cls.objects.filter(user=user)
