import textwrap

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from coldfront.core.project.models import (Project, ProjectAdminComment,
                                            ProjectReview, ProjectStatusChoice,
                                            ProjectUser, ProjectUserMessage,
                                            ProjectUserRoleChoice,
                                            ProjectUserStatusChoice)
from coldfront.core.organization.models import Organization


@admin.register(ProjectStatusChoice)
class ProjectStatusChoiceAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(ProjectUserRoleChoice)
class ProjectUserRoleChoiceAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(ProjectUserStatusChoice)
class ProjectUserStatusChoiceAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(ProjectUser)
class ProjectUserAdmin(SimpleHistoryAdmin):
    fields_change = ('user', 'project', 'role', 'status', 'created', 'modified', )
    readonly_fields_change = ('user', 'project', 'created', 'modified', )
    list_display = ('pk', 'project_title', 'PI', 'User', 'role', 'status',
                    'created', 'modified',)
    list_filter = ('role', 'status')
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    raw_id_fields = ('user', 'project')

    def project_title(self, obj):
        return textwrap.shorten(obj.project.title, width=50)

    def PI(self, obj):
        return '{} {} ({})'.format(obj.project.pi.first_name, obj.project.pi.last_name, obj.project.pi.username)

    def User(self, obj):
        return '{} {} ({})'.format(obj.user.first_name, obj.user.last_name, obj.user.username)

    def get_fields(self, request, obj):
        if obj is None:
            return super().get_fields(request)
        else:
            return self.fields_change

    def get_readonly_fields(self, request, obj):
        if obj is None:
            # We are adding an object
            return super().get_readonly_fields(request)
        else:
            return self.readonly_fields_change

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            # We are adding an object
            return super().get_inline_instances(request)
        else:
            return [inline(self.model, self.admin_site) for inline in self.inlines]


class ProjectUserInline(admin.TabularInline):
    model = ProjectUser
    fields = ['user', 'project', 'role', 'status', 'enable_notifications', ]
    readonly_fields = ['user', 'project', ]
    extra = 0


class ProjectAdminCommentInline(admin.TabularInline):
    model = ProjectAdminComment
    extra = 0
    fields = ('comment', 'author', 'created'),
    readonly_fields = ('author', 'created')


class ProjectUserMessageInline(admin.TabularInline):
    model = ProjectUserMessage
    extra = 0
    fields = ('message', 'author', 'created'),
    readonly_fields = ('author', 'created')

class ProjAllOrgsListFilter(admin.SimpleListFilter):
    """Filter for Project Admin page, to filter by Organization.

    Will allow filtering by any Organization associated with a 
    Project (either as primary_organization or additional_organization).
    We also include all ancestors of such in the hierarchy, so that
    e.g. selecting on a "college" will include all Projects associated
    with "departments" belonging to the specified college.
    """

    title = "Organization Membership (hierachical)"
    parameter_name = "organization"

    def lookups(self, request, model_admin):
        """Gets list of all orgs which are connected with a project

        Includes both primary and addition_organizations, and any
        ancestor organizations.
        """

        # This gets a list of lists
        all_orgs = map(lambda x: x.all_organizations(),
            Project.objects.all())
        # Flatten into a simple list, dedup, etc
        all_orgs = list(set([ org for sublist in all_orgs for org in sublist]))
        # Add parent orgs
        all_orgs = Organization.add_parents_to_organization_list(all_orgs)
        # Sort by full code
        all_orgs.sort(key=lambda x: x.fullcode())
        # Convert to list of tuples:
        #   coded value is pk of org
        #   display value is semi-fullcode of org
        lookup_list = map(lambda x: (x.pk, x.semifullcode()), all_orgs)
        return lookup_list

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        tmp = Organization.objects.filter(pk=self.value()).all()
        if tmp:
            parent_org = tmp[0]
            oset = parent_org.descendents()
            oset.append(parent_org)
        else:
            oset = []

        # Find those matching in primary_organization
        qs1 = queryset.filter(primary_organization__in=oset)
        # Find those matching in additional_organizations
        qs2 = queryset.filter(additional_organizations__in=oset)

        # Union them
        qs1.union(qs2)
        return qs1

@admin.register(Project)
class ProjectAdmin(SimpleHistoryAdmin):
    fields_change = ('title', 'pi', 'description', 'status', 'requires_review', 'force_review', 'created', 'modified',
            'primary_organization', 'additional_organizations')
    readonly_fields_change = ('created', 'modified', )
    list_display = ('pk', 'title', 'PI', 'created', 'modified', 'status', 'primary_organization')
    search_fields = ['pi__username', 'projectuser__user__username',
                     'projectuser__user__last_name', 'projectuser__user__last_name', 'title']
    list_filter = ('status', 'force_review', ProjAllOrgsListFilter )
    inlines = [ProjectUserInline, ProjectAdminCommentInline, ProjectUserMessageInline]
    raw_id_fields = ['pi', ]
    filter_horizontal = ['additional_organizations', ]

    def PI(self, obj):
        return '{} {} ({})'.format(obj.pi.first_name, obj.pi.last_name, obj.pi.username)

    def get_fields(self, request, obj):
        if obj is None:
            return super().get_fields(request)
        else:
            return self.fields_change

    def get_readonly_fields(self, request, obj):
        if obj is None:
            # We are adding an object
            return super().get_readonly_fields(request)
        else:
            return self.readonly_fields_change

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            # We are adding an object
            return []
        else:
            return super().get_inline_instances(request)

    def save_formset(self, request, form, formset, change):
        if formset.model in [ProjectAdminComment, ProjectUserMessage]:
            instances = formset.save(commit=False)
            for instance in instances:
                instance.author = request.user
                instance.save()
        else:
            formset.save()


@admin.register(ProjectReview)
class ProjectReviewAdmin(SimpleHistoryAdmin):
    list_display = ('pk', 'project', 'PI', 'reason_for_not_updating_project', 'created', 'status')
    search_fields = ['project__pi__username', 'project__pi__first_name', 'project__pi__last_name',]
    list_filter = ('status', )

    def PI(self, obj):
        return '{} {} ({})'.format(obj.project.pi.first_name, obj.project.pi.last_name, obj.project.pi.username)

