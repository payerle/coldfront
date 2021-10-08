from django.contrib import admin

from coldfront.core.organization.models import Organization, OrganizationLevel


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
        'code',
        'parent',
        'organization_level',
        'shortname',
        'longname',
    )
    search_fields = ['name', 'level']
    #list_filter = ('is_selectable', )
