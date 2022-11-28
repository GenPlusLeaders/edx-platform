from adminsortable2.admin import SortableInlineAdminMixin
from django.contrib import admin

from openedx.features.genplus_features.genplus_learning import \
    models as learning_models


@admin.register(learning_models.ClassLesson)
class ClassLessonAdmin(admin.ModelAdmin):
    list_display = (
        'class_unit',
        'usage_key',
        'is_locked',
    )
    readonly_fields = ('class_unit', 'usage_key', 'course_key',)


@admin.register(learning_models.YearGroup)
class YearGroupAdmin(admin.ModelAdmin):
    search_fields = ('name', 'program_name',)


# TODO: Remove this after testing
@admin.register(learning_models.ProgramEnrollment)
class ProgramEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'gen_class', 'program', 'status',)
    readonly_fields = ('student', 'gen_class', 'program',)


@admin.register(learning_models.ProgramUnitEnrollment)
class ProgramUnitEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('program_enrollment', 'course',)
    readonly_fields = ('program_enrollment', 'course', 'course_enrollment',)


class UnitInline(SortableInlineAdminMixin, admin.TabularInline):
    model = learning_models.Unit

    def get_readonly_fields(self, request, obj):
        if isinstance(obj, learning_models.Program) and not obj.is_unpublished:
            return ['course']

        return self.readonly_fields

    def has_add_permission(self, request, obj):
        if isinstance(obj, learning_models.Program) and obj.is_unpublished:
            return True
        return False

    def has_delete_permission(self, request, obj):
        if isinstance(obj, learning_models.Program) and obj.is_unpublished:
            return True
        return False


@admin.register(learning_models.Program)
class ProgramAdmin(admin.ModelAdmin):
    inlines = [
        UnitInline,
    ]
    search_fields = ('year_group__name',)
    list_display = (
        'year_group',
        'start_date',
        'end_date',
        'status',
    )
    readonly_fields = ('slug', 'uuid',)


@admin.register(learning_models.ClassUnit)
class ClassUnitAdmin(admin.ModelAdmin):
    list_display = ('gen_class', 'unit',)
    readonly_fields = ('gen_class', 'unit',)


admin.site.register(learning_models.UnitCompletion)
admin.site.register(learning_models.UnitBlockCompletion)
