import re
import logging
import pafy
from django.db import models
from django_extensions.db.models import TimeStampedModel
from html import unescape
from django.utils.html import strip_tags
from tinymce.models import HTMLField
from openedx.features.genplus_features.genplus.models import Skill, Teacher


logger = logging.getLogger(__name__)


class Gtcs(TimeStampedModel):
    name = models.CharField(unique=True, max_length=1024)

    def __str__(self):
        return self.name


class MediaType(models.Model):
    name = models.CharField(unique=True, max_length=255)

    def __str__(self):
        return self.name


class Article(TimeStampedModel):
    title = models.CharField(max_length=1024)
    cover = models.ImageField(upload_to='article_covers',
                              help_text='Upload the cover for the article')
    skills = models.ManyToManyField(Skill, related_name='articles')
    gtcs = models.ManyToManyField(Gtcs, related_name='articles')
    media_types = models.ManyToManyField(MediaType, related_name='articles')
    content = HTMLField()
    author = models.CharField(max_length=1024, help_text='Add name of the author')
    time = models.PositiveIntegerField(default=0, help_text='Time required to read/watch/listen the article')
    is_draft = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def is_completed(self, teacher):
        return ReflectionAnswer.objects.filter(reflection__article=self,
                                               teacher=teacher).exists()

    def is_rated(self, teacher):
        return ArticleRating.objects.filter(article=self,
                                            teacher=teacher).exists()

    def save(self, **kwargs):
        read_time = self.get_read_time(self.title, self.content)
        watch_time = self.get_video_time(self.content)
        self.time = read_time + watch_time
        super().save(**kwargs)

    @staticmethod
    def get_read_time(title, content):
        string = title + unescape(strip_tags(content))
        total_words = len(string.split())
        return round(total_words / 200)

    def get_video_time(self, content):
        video_time = 0
        links = re.findall(r'(https?://www.youtube.com\S+)', content)
        for link in links:
            watch_link = link.replace('"', ' ').replace('embed/', '?v=')
            video_time += self.get_yt_video_time(watch_link)

        return video_time

    @staticmethod
    def get_yt_video_time(link):
        try:
            video_metadata = pafy.new(link)
            t = 0
            for u in video_metadata.duration.split(':'):
                t = 60 * t + int(u)
            return t/60
        except Exception as e:
            logger.exception(e)


class Reflection(TimeStampedModel):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='reflections')
    title = models.TextField()

    def __str__(self):
        return self.title


class ReflectionAnswer(TimeStampedModel):
    reflection = models.ForeignKey(Reflection, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    answer = models.TextField()

    class Meta:
        unique_together = ('reflection', 'teacher')


class FavoriteArticle(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='favorite_articles')
    article = models.ForeignKey(Article, on_delete=models.CASCADE)


class ArticleRating(TimeStampedModel):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=0)
    comment = models.TextField()

    class Meta:
        unique_together = ('teacher', 'article')


# model to log the view, view count and engagement time on an article
class ArticleViewLog(TimeStampedModel):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0, help_text='Views count on each article.')
    engagement = models.PositiveIntegerField(default=0, help_text='Length of engagement (minutes/seconds)')
