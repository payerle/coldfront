from django.contrib import admin

from coldfront.core.user.models import UserProfile

from coldfront.core.organization.models import Organization

class UserAllOrgsListFilter(admin.SimpleListFilter):
    title = "Organization Membership (hierarchical)"
    parameter_name = "organization"

    def lookups(self, request, model_admin):
        """Get list of all orgs which are connected with an user.

        Includes both primary and additional_organizations, and
        any ancestor organizations.
        """

        # This gets a list of lists
        all_orgs = map(lambda x: x.all_organizations(),
                UserProfile.objects.all())
        # flatten into a simple list, dedup, etc
        all_orgs = list(set([org for sublist in all_orgs for org in sublist]))
        # Add parent orgs
        all_orgs = Organization.add_parents_to_organization_list(all_orgs)
        # Sort by fullcode
        all_orgs.sort(key=lambda x: x.fullcode())
        # Convert to list of tuples:
        #   coded value is pk of org
        #   display is semi-fullcode of org
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

        # Find those matching in primary organization
        qs1 = queryset.filter(primary_organization__in=oset)
        # Find those mathcing in additional_organizations
        qs2 = queryset.filter(additional_organizations__in=oset)

        # Union them
        qs1.union(qs2)
        return qs1

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'is_pi', 'primary_organization')
    list_filter = ('is_pi', UserAllOrgsListFilter )
    search_fields = ['user__username', 'user__first_name', 'user__last_name']


    def username(self, obj):
        return obj.user.username

    def first_name(self, obj):
        return obj.user.first_name

    def last_name(self, obj):
        return obj.user.last_name

    #def primary_organization(self, obj):
    #    return obj.primary_organization.semifullcode
