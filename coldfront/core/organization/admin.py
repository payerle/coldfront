from django.contrib import admin

from coldfront.core.organization.models import Organization, OrganizationLevel
from coldfront.core.organization.models import Directory2Organization


@admin.register(OrganizationLevel)
class OrganizationLevelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'level',
        'parent',
    )
    search_fields = ['name', 'level']

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        'fullcode',
        'parent',
        'organization_level',
        'shortname',
        'longname',
    )
    search_fields = ['name', 'level']
    #list_filter = ('is_selectable', )

@admin.register(Directory2Organization)
class Directory2OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        'organization',
        'directory_string',
    )
    search_fields = ['directory_string', 'organization']
    #list_filter = ('is_selectable', )
