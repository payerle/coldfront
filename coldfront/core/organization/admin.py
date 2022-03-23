from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple

from coldfront.core.organization.models import (
    Organization, OrganizationLevel, Directory2Organization)

from coldfront.core.user.models import UserProfile
from coldfront.core.project.models import Project

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
        'is_selectable_for_user',
        'is_selectable_for_project',
    )
    fields_change = (
        'fullcode',
        'parent',
        'organization_level',
        'shortname',
        'longname',
        'is_selectable_for_user',
        'is_selectable_for_project',
    )
    search_fields = ['code',]


@admin.register(Directory2Organization)
class Directory2OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        'organization',
        'directory_string',
    )
