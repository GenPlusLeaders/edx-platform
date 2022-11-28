import django_filters

from openedx.features.genplus_features.genplus.models import Teacher
from openedx.features.genplus_features.genplus_teach.models import (Article,
                                                                    Gtcs,
                                                                    MediaType)


class ArticleFilter(django_filters.FilterSet):
    skill = django_filters.NumberFilter(
        field_name='skills__id',
    )
    media_type = django_filters.NumberFilter(
        field_name='media_types__id',
    )
    gtcs = django_filters.NumberFilter(
        field_name='gtcs__id',
    )
    is_completed = django_filters.BooleanFilter(method='filter_is_completed')

    def filter_is_completed(self, queryset, name, value):
        teacher = Teacher.objects.get(gen_user__user=self.request.user)
        try:
            article_ids = [
                    article.pk
                    for article in queryset.all()
                    if article.is_completed(teacher) == value
                ]
            return queryset.filter(id__in=article_ids)
        except ValueError:
            pass
        return queryset

    class Meta:
        model = Article
        fields = ('title', 'skill', 'media_types', 'gtcs')
