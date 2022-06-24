from django.contrib import admin
from .models import Unit, Lesson


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = (
        'display_name',
        'course_key',
        'year_group',
        'is_locked',
    )
    readonly_fields = ('course_key',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        'unit',
        'usage_key',
        'is_locked',
    )
    readonly_fields = ('unit', 'usage_key')
