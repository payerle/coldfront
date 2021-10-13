from django.core.management.base import BaseCommand

from coldfront.core.organization.models import \
    OrganizationLevel, Organization
                                        


class Command(BaseCommand):
    help = 'Add default organization related entries'

    def handle(self, *args, **options):

        # Create default OrganizationLevels
        orglevels = [
            # Name, level, ParentName
            [ 'University', 40, None ],
            [ 'College', 30, 'University' ],
            [ 'Department', 20, 'College' ],
        ]
        for rec in orglevels:
            oname = rec[0]
            level = rec[1]
            pname = rec[2]
            parent = None
            if pname is not None:
                parent = OrganizationLevel.objects.get(name=pname)
            OrganizationLevel.objects.get_or_create(
                name=oname, level=level, parent=parent)

        # Create a top-level 'Unknown' organization
        univ = OrganizationLevel.objects.get(name='University')
        Organization.objects.get_or_create(
                code='Unknown', 
                organization_level=univ,
                parent=None,
                shortname='Unknown',
                longname='Container for Unknown organizations'
        )
        return