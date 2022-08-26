import django_filters
from openedx.features.genplus_features.genplus_teach.models import MediaType, Gtcs, Article


class ArticleFilter(django_filters.FilterSet):
    skills = django_filters.CharFilter(
        field_name='skills__name',
        lookup_expr='exact',
    )
    media_type = django_filters.NumberFilter(
        field_name='media_types__id',
    )
    gtcs = django_filters.CharFilter(
        field_name='gtcs__name',
        lookup_expr='contains',
    )

    class Meta:
        model = Article
        fields = ('title', 'skills', 'media_types', 'gtcs')
