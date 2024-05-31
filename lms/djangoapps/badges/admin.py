"""
Admin registration for Badge Models
"""


from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from lms.djangoapps.badges.models import (
    BadgeAssertion,
    BadgeClass,
    CourseCompleteImageConfiguration,
    CourseEventBadgesConfiguration
)


@admin.register(BadgeClass)
class BadgeClassAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'slug', 'issuing_component', 'course_id')
    list_filter = ('slug', )


admin.site.register(CourseCompleteImageConfiguration)
admin.site.register(BadgeAssertion)
# Use the standard Configuration Model Admin handler for this model.
admin.site.register(CourseEventBadgesConfiguration, ConfigurationModelAdmin)
