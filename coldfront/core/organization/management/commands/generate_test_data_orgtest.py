import sys

from django.core.management.base import BaseCommand, CommandError

from coldfront.core.organization.models import (
        OrganizationLevel, 
        Organization,
        )
from django.contrib.auth.models import (
        User,
        )
from coldfront.core.user.models import (
        UserProfile,
        )
from coldfront.core.resource.models import (
        Resource,
        ResourceType,
        ResourceAttribute,
        ResourceAttributeType,
        )
from coldfront.core.project.models import (
        Project, 
        ProjectStatusChoice,
        ProjectUser,
        ProjectUserRoleChoice,
        ProjectUserStatusChoice,
        )
from coldfront.core.allocation.models import (
        Allocation, 
        AllocationAttribute,
        AllocationAttributeType,
        AllocationStatusChoice,
        AllocationUser,
        AllocationUserStatusChoice,
        )
from coldfront.core.field_of_science.models import (
        FieldOfScience,
        )
                                        
                                        


class Command(BaseCommand):
    help = 'Setup orgtest data'

    def verbose_msg(self, options, message, level=0):
        """Print message if verbosity > level."""
        verbosity = options['verbosity']
        if verbosity > level:
            label = 'DEBUG'
            if level:
                label = 'DEBUG{}'.format(level)
            message.strip()
            text = '[{}] {}\n'.format(label, message)
            sys.stderr.write(text)
        return

    def create_org_levels(self, options):
        """Create OrgLevels for test data"""
        self.verbose_msg(options, 'Creating OrganizationLevels as needed')
        orglevels = [
            { 
                'name':'University', 
                'level': 40, 
                'parent': None,
            },
            { 
                'name': 'College', 
                'level': 30, 
                'parent': 'University',
            },
            { 
                'name': 'Department', 
                'level': 20, 
                'parent': 'College',
            },
        ]

        for rec in orglevels:
            args = {}
            args['name'] = rec['name']
            args['level'] = rec['level']
            parent = None
            if 'parent' in rec:
                pname = rec['parent']
                if pname is not None:
                    parent = OrganizationLevel.objects.get(name=pname)
            args['parent'] = parent

            obj, created = OrganizationLevel.objects.get_or_create(**args)
            if created:
                self.verbose_msg(options, 
                        'Created OrganizationLevel {}'.format(obj),
                        1)
            else:
                self.verbose_msg(options, 
                        'OrganizationLevel {} already exists, not creating'.format(obj),
                        2)
        return

    def create_orgs(self, options):
        """Create Orgs for test data"""
        self.verbose_msg(options, 'Creating Organizations as needed')
        orgs = [
                # University level
                {   'code': 'Unknown',
                    'organization_level': 'University',
                    'parent': None,
                    'shortname': 'Unknown',
                    'longname': 'Container for Unknown organizations',
                    'is_selectable_for_user': False,
                    'is_selectable_for_project': False,
                },
                {   'code': 'UMD',
                    'organization_level': 'University',
                    'parent': None,
                    'shortname': 'UMCP',
                    'longname': 'University of Maryland',
                    'is_selectable_for_user': False,
                    'is_selectable_for_project': False,
                },
                {   'code': 'UMB',
                    'organization_level': 'University',
                    'parent': None,
                    'shortname': 'UMD Baltimore',
                    'longname': 'University of Maryland, Baltimore',
                    'is_selectable_for_user': False,
                    'is_selectable_for_project': False,
                },
                # College level - UMD
                {   'code': 'CMNS',
                    'organization_level': 'College',
                    'parent': 'UMD',
                    'shortname': 'CMNS',
                    'longname': 'College of Computer, Mathematical, and Natural Sciences',
                    'is_selectable_for_user': False,
                    'is_selectable_for_project': False,
                },
                {   'code': 'ENGR',
                    'organization_level': 'College',
                    'parent': 'UMD',
                    'shortname': 'Engineering',
                    'longname': 'School of Engineering',
                    'is_selectable_for_user': False,
                    'is_selectable_for_project': False,
                },
                # Departmental level - UMD-CMNS
                {   'code': 'ASTR',
                    'organization_level': 'Department',
                    'parent': 'UMD-CMNS',
                    'shortname': 'Astronomy',
                    'longname': 'Astronomy Department',
                    'is_selectable_for_user': True,
                    'is_selectable_for_project': True,
                },
                {   'code': 'PHYS',
                    'organization_level': 'Department',
                    'parent': 'UMD-CMNS',
                    'shortname': 'Physics',
                    'longname': 'Physics Department',
                    'is_selectable_for_user': True,
                    'is_selectable_for_project': True,
                },
                # Departmental level - UMD-ENGR
                {   'code': 'ENAE',
                    'organization_level': 'Department',
                    'parent': 'UMD-ENGR',
                    'shortname': 'Aeronautical Eng',
                    'longname': 'Dept of Aeronautical Engineering',
                    'is_selectable_for_user': True,
                    'is_selectable_for_project': True,
                },
                {   'code': 'ENMA',
                    'organization_level': 'Department',
                    'parent': 'UMD-ENGR',
                    'shortname': 'Materials Eng',
                    'longname': 'Dept of Materials Engineering',
                    'is_selectable_for_user': True,
                    'is_selectable_for_project': True,
                },
                # College level - UMB
                {   'code': 'SoM',
                    'organization_level': 'College',
                    'parent': 'UMB',
                    'shortname': 'Medicine',
                    'longname': 'School of Medicine',
                    'is_selectable_for_user': False,
                    'is_selectable_for_project': False,
                },
                {   'code': 'SoD',
                    'organization_level': 'College',
                    'parent': 'UMB',
                    'shortname': 'Dentistry',
                    'longname': 'School of Dentistry',
                    'is_selectable_for_user': False,
                    'is_selectable_for_project': False,
                },
                # Departmental level - UMB-SoM
                {   'code': 'Psych',
                    'organization_level': 'Department',
                    'parent': 'UMB-SoM',
                    'shortname': 'Psychiatry',
                    'longname': 'Psychiatry Department',
                    'is_selectable_for_user': True,
                    'is_selectable_for_project': True,
                },
                {   'code': 'Surg',
                    'organization_level': 'Department',
                    'parent': 'UMB-SoM',
                    'shortname': 'Surgery',
                    'longname': 'Surgery Department',
                    'is_selectable_for_user': True,
                    'is_selectable_for_project': True,
                },
                # Departmental level - UMB-SoD
                {   'code': 'NeuPain',
                    'organization_level': 'Department',
                    'parent': 'UMB-SoD',
                    'shortname': 'Neural and Pain',
                    'longname': 'Department of Neural and Pain Sciences',
                    'is_selectable_for_user': True,
                    'is_selectable_for_project': True,
                },
                {   'code': 'Perio',
                    'organization_level': 'Department',
                    'parent': 'UMB-SoD',
                    'shortname': 'Periodontics',
                    'longname': 'Division of Periodontics',
                    'is_selectable_for_user': True,
                    'is_selectable_for_project': True,
                },
            ]
                    
        for rec in orgs:
            args = {}
            args['code'] = rec['code']

            if 'shortname' in rec:
                args['shortname'] = rec['shortname']
            if 'longname' in rec:
                args['longname'] = rec['longname']
            if 'is_selectable_for_user' in rec:
                args['is_selectable_for_user'] = rec['is_selectable_for_user']
            if 'is_selectable_for_project' in rec:
                args['is_selectable_for_project'] = rec['is_selectable_for_project']

            olevname = rec['organization_level']
            olev = OrganizationLevel.objects.get(name=olevname)
            args['organization_level'] = olev

            pname = rec['parent']
            if pname is None:
                parent = None
            else:
                parent = Organization.get_organization_by_fullcode(pname)
                args['parent'] = parent

            obj, created, changed = Organization.create_or_update_organization(
                    args)
            if created:
                self.verbose_msg(options, 
                        'Created Organization {}'.format(obj),
                        1)
            else:
                self.verbose_msg(options, 
                        'Organization {} already exists, not creating'.format(obj),
                        2)
        return

    def create_users(self, options):
        """Create Users for test data"""
        self.verbose_msg(options, 'Creating Users as needed')
        users = [
                # Users
                {   'username': 'newton',
                    'first_name': 'Isaac',
                    'last_name': 'Newton',
                    'primary_department': 'UMD-CMNS-PHYS',
                    'is_pi': False,
                },
                {   'username': 'einstein',
                    'first_name': 'Albert',
                    'last_name': 'Einstein',
                    'primary_department': 'UMD-CMNS-PHYS',
                    'is_pi': True,
                },
                {   'username': 'freud',
                    'first_name': 'Sigmund',
                    'last_name': 'Freud',
                    'primary_department': 'UMB-SoM-Psych',
                    'is_pi': True,
                },
                {   'username': 'hawkeye',
                    'first_name': 'Benjamin',
                    'last_name': 'Pierce',
                    'primary_department': 'UMB-SoM-Surg',
                    'is_pi': True,
                },
                {   'username': 'orville',
                    'first_name': 'Orville',
                    'last_name': 'Wright',
                    'primary_department': 'UMD-ENGR-ENAE',
                    'is_pi': True,
                },
                {   'username': 'wilbur',
                    'first_name': 'Wilbur',
                    'last_name': 'Wright',
                    'primary_department': 'UMD-ENGR-ENAE',
                    'is_pi': False,
                },
            ]


        for urec in users:
            args = {}
            uname = urec['username']
            args['username'] = uname
            lname = urec['last_name']
            args['last_name'] = lname
            fname = urec['first_name']
            args['first_name'] = fname
            if 'email' in urec:
                email = urec['email']
            else:
                email = '{}@example.com'.format(uname)
            args['email'] = email
            user, created = User.objects.get_or_create(**args)
            if created:
                self.verbose_msg(options, 'Created User {} ({} {})'.format(
                    user.username, fname, lname), 1)
            else:
                self.verbose_msg(options, 
                        'User {} ({} {}) already exists, not creating'.format(
                            user.username,
                            fname,
                            lname), 2)
            
            args = {    'user': user}
            if 'primary_organization' in urec:
                args['primary_organization'] = urec['primary_organization']
            if 'ispi' in urec:
                args['is_pi'] = urec['is_pi']
            if 'additional_organizations' in urec:
                args['additional_organizations'] = urec['additional_organizations']

            # And generate UserProfile if needed
            qset = UserProfile.objects.filter(user=user)
            if qset:
                created = False
                changed = False
                obj = qset[0]
                if 'is_pi' in args:
                    if obj.is_pi != args['is_pi']:
                        obj.is_pi = args['ispi']
                        changed = True
                if 'primary_organization' in args:
                    if obj.primary_organization != args['primary_organization']:
                        obj.primary_organization = (
                                args['primary_organization'].pk )
                        changed = True
                if 'additional_organizations' in args:
                    if obj.additional_organizations != args['additional_organizations']:
                        obj.additional_organizations = args['additional_organizations']
                        changed = True

                if changed:
                    obj.save()
            else:
                created = True
                obj = UserProfile.objects.get_or_create(args)

            if created:
                self.verbose_msg(options,
                        'Created UserProfile for {}'.format(uname),
                        1)
            else:
                self.verbose_msg(options, 
                        'UserProfile for  {} already exists, not creating'.format(
                            uname), 2)

        return

    def create_resources(self, options):
        """Create Resources for test data"""
        self.verbose_msg(options, 'Creating Resources as needed')
        resources = [
                { 
                    'name': 'University HPC',
                    'description': 'Main University HPC',
                    'is_available': True,
                    'is_public': True,
                    'is_allocatable': True,
                    'requires_payment': False,
                    'parent_resource': None,
                    'resource_type': 'Cluster',
                    'resource_attributes': [
                        {   'resource_attribute_type': 'slurm_cluster',
                            'value': 'mainhpc',
                        },
                    ],
                },
            ]

        for rec in resources:
            args = {}
            name = rec['name']
            args['name'] = name

            restype = rec['resource_type']
            rtype = ResourceType.objects.get(name=restype)
            args['resource_type'] = rtype

            if 'description' in rec:
                desc = rec['description']
            else:
                desc = name
            args['description'] = desc

            if 'is_available' in rec:
                args['is_available'] = rec['is_available']
            if 'is_public' in rec:
                args['is_public'] = rec['is_public']
            if 'is_allocatable' in rec:
                args['is_allocatable'] = rec['is_allocatable']
            if 'requires_payment' in rec:
                args['requires_payment'] = rec['requires_payment']

            if 'parent_resource' in rec:
                parent_resource = rec['parent_resource']
                if parent_resource is not None:
                    parent = Resource.objects.get(name=parent_resource)
                    args['parent'] = parent

            if 'resource_attributes' in rec:
                rattribs = rec['resource_attributes']
            else:
                rattribs = []

            res, created = Resource.objects.get_or_create(**args)
            if created:
                self.verbose_msg(options, 
                        'Created Resource {}'.format(res), 1)
            else:
                self.verbose_msg(options,
                        'Resource {} already exists, not creating'.format(res),
                        2)

            # And create and needed resource_attributes
            for rarec in rattribs:
                ratname = rarec['resource_attribute_type']
                ratype = ResourceAttributeType.objects.get(name=ratname)
                value = rarec['value']
                args = { 
                        'resource_attribute_type': ratype,
                        'value': value,
                        'resource': res,
                        }
                raobj, created = ResourceAttribute.objects.get_or_create(**args)
                if created:
                    self.verbose_msg(options,
                            'Created ResourceAttribute {} with '
                            'value {} for Resource {}'.format(raobj, value, res),
                            1)
                else:
                    self.verbose_msg(options,
                            'ResourceAttribute {} with value {} '
                            'for Resource {} already exists, not creating'.format(
                                raobj, value, res),
                            2)

        return

    def create_projects(self, options):
        """Create Projects for test data"""
        self.verbose_msg(options, 'Creating Projects as needed')
        projects = [
                { 
                    'title': 'Gravitational Studies',
                    'description': 'Study of Gravity',
                    'pi_username': 'einstein',
                    'field_of_science': 'Gravitational Physics',
                    'force_review': False,
                    'requires_review': True,
                    'primary_organization': 'UMD-CMNS-PHYS',
                    'additional_organizations': [],
                    'users':
                        [   'newton',
                        ],
                    'managers':
                        [   'einstein',
                        ]
                },
                { 
                    'title': 'Hyposonic Flight',
                    'description': 'Study of Flight at very low speeds',
                    'pi_username': 'orville',
                    'field_of_science': 'Other',
                    'force_review': False,
                    'requires_review': True,
                    'primary_organization': 'UMD-ENGR-ENAE',
                    'additional_organizations': [],
                    'users':
                        [   'wilbur',
                        ],
                    'managers':
                        [   'orville',
                        ]
                },
                { 
                    'title': 'Artificial Id',
                    'description': 'Attempts to build artificial intelligence with ego and id',
                    'pi_username': 'freud',
                    'field_of_science': 'Information, Robotics, and Intelligent Systems',
                    'force_review': False,
                    'requires_review': True,
                    'primary_organization': 'UMB-SoM-Psych',
                    'additional_organizations': [],
                },
                { 
                    'title': 'Meatball Surgery',
                    'description': 'Surgery under battlefield conditions',
                    'pi_username': 'hawkeye',
                    'field_of_science': 'Physiology and Behavior',
                    'force_review': False,
                    'requires_review': True,
                    'primary_organization': 'UMB-SoM-Surg',
                    'additional_organizations': [],
                },

            ]

        active_status = None
        for rec in projects:
            args = {}
            title = rec['title']
            args['title'] = title

            if 'pi_username' in rec:
                pi_username = rec['pi_username']
                qset = User.objects.filter(username=pi_username)
                if qset:
                    tmp = qset[0]
                pi = User.objects.get(username=pi_username)
                args['pi'] = pi

            if 'description' in rec:
                desc = rec['description']
                args['description'] = desc

            if 'status' in rec:
                status = ProjectStatusChoice.objects.get(name=rec['status'])
                args['status'] = status
            else:
                # Default to 'Active'
                if active_status is None:
                    active_status = ProjectStatusChoice.objects.get(
                            name='Active')
                args['status'] = active_status

            if 'field_of_science' in rec:
                fosname = rec['field_of_science']
                fos = FieldOfScience.objects.get(description=fosname)
                args['field_of_science'] = fos

            if 'force_review' in rec:
                args['force_review'] = rec['force_review']
            if 'requires_review' in rec:
                args['requires_review'] = rec['requires_review']

            if 'primary_organization' in rec:
                porg = Organization.get_organization_by_fullcode(
                        rec['primary_organization'])
                args['primary_organization'] = porg

            if 'additional_organziations' in rec:
                aorgs = rec['additional_organizations']
                addorgs = []
                for aorgcode in aorgs:
                    aorg = Organization.get_organization_by_fullcode(aorgcode)
                    addorgs.append(aorg)
                args['additional_organizations'] = addorgs

            obj, created = Project.objects.get_or_create(**args)
            if created:
                self.verbose_msg(options, 
                        'Created Project {}'.format(obj), 1)
            else:
                self.verbose_msg(options,
                        'Project {} already exists, not creating'.format(obj),
                        2)

            # And create project users
            managers = []
            role = ProjectUserRoleChoice.objects.get(name='Manager')
            status = ProjectUserStatusChoice.objects.get(name='Active')
            if 'managers' in rec:
                mgrs = rec['managers']
                for mgr in mgrs:
                    user = User.objects.get(username=mgr)
                    managers.append(user)
            else:
                managers = [ pi ]
            for user in managers:
                args = {
                        'user': user,
                        'project': obj,
                        'role': role,
                        'status': status,
                        'enable_notifications': True,
                    }
                puser, created = ProjectUser.objects.get_or_create(**args)
                if created:
                    self.verbose_msg(options, 
                            'Added ProjUser {} to Project {} as manager'.format(
                                puser, obj), 1)
                else:
                    self.verbose_msg(options,
                            'ProjectUser {} already in Project P{{, not creating'.format(
                                puser, obj), 2)

            users = []
            role = ProjectUserRoleChoice.objects.get(name='User')
            if 'users' in rec:
                usrs = rec['users']
                for usr in usrs:
                    user = User.objects.get(username=usr)
                    users.append(user)
                for user in users:
                    args = {
                            'user': user,
                            'project': obj,
                            'role': role,
                            'status': status,
                            'enable_notifications': True,
                        }
                    puser, created = ProjectUser.objects.get_or_create(**args)
                    if created:
                        self.verbose_msg(options, 
                                'Added ProjUser {} to Project {} as user'.format(
                                    puser, obj), 1)
                    else:
                        self.verbose_msg(options,
                                'ProjectUser {} already in Project P{{, not creating'.format(
                                    puser, obj), 2)

        return

    def create_allocations(self, options):
        """Create Allocations for test data"""
        self.verbose_msg(options, 'Creating Allocations as needed')
        allocations = [
                { 
                    'description': 'freud-alloc',
                    'project': 'Artificial Id',
                    'resources': ['University HPC' ],
                    # 'status': 
                    # 'quantity':
                    # 'justification': 
                    # 'is-locked':
                    # 'users':
                    'allocation_attributes': [
                        {   'allocation_attribute_type': 'slurm_account_name',
                            'value': 'freud-alloc',
                        },
                    ],

                },
                { 
                    'description': 'hawkeye-alloc',
                    'project': 'Meatball Surgery',
                    'resources': ['University HPC' ],
                    # 'status': 
                    # 'quantity':
                    # 'justification': 
                    # 'is-locked':
                    # 'users':
                    'allocation_attributes': [
                        {   'allocation_attribute_type': 'slurm_account_name',
                            'value': 'hawkeye-alloc',
                        },
                    ],

                },
            ]

        for rec in allocations:
            args = {}

            pname = rec['project']
            if pname is not None:
                proj = Project.objects.get(title=pname)
                args['project'] = proj

            if 'quantity' in rec:
                args['quantity'] = rec['quantity']

            if 'is_locked' in rec:
                args['is_locked'] = rec['is_locked']

            if 'status' in rec:
                status_name = rec['status']
            else:
                status_name = 'Active'

            status = AllocationStatusChoice.objects.get(name=status_name)
            args['status'] = status

            if 'justification' in rec:
                args['justification'] = rec['justification']

            alloc, created = Allocation.objects.get_or_create(**args)

            if created:
                self.verbose_msg(options, 
                        'Created Allocation {}'.format(alloc.description), 1)
            else:
                self.verbose_msg(options,
                        'Allocation {} already exists, not creating'.format(
                            alloc.description), 2)

            # Add Resources to Allocation
            resources = []
            if 'resources' in rec:
                rsrcs = rec['resources']
                for rsrc in rsrcs:
                    resource = Resource.objects.get(name=rsrc)
                    resources.append(resource)
            for resource in resources:
                alloc.resources.add(resource)

            # And create allocation users
            users = None
            if 'users' in rec:
                unames = rec['users']
                users = []
                for uname in unames:
                    user = User.objects.get(username=uname)
                    users.append(user)
            else:
                # Default to active all ProjectUsers for this Project
                pusers = ProjectUser.objects.filter(
                        project__title=pname,
                        status__name='Active')
                users = [ x.user for x in pusers ]
            status = AllocationUserStatusChoice.objects.get(name='Active')
            for user in users:
                args={
                        'status': status,
                        'allocation': alloc,
                        'user': user,
                        }
                obj, created = AllocationUser.objects.get_or_create(**args)
                if created:
                    self.verbose_msg(options,
                            'Created AllocationUser {} for Alloc {}'.format(
                                obj, alloc), 1)
                else:
                    self.verbose_msg(options,
                            'AllocationUser {} for Alloc {} already exists'.format(
                                obj, alloc), 2)

            # And add allocation attributes
            aattribs = None
            if 'allocation_attributes' in rec:
                aattribs = rec['allocation_attributes']
                for aarec in aattribs:
                    aatname = aarec['allocation_attribute_type']
                    aatype = AllocationAttributeType.objects.get(name=aatname)
                    value = aarec['value']
                    args = {
                            'allocation_attribute_type': aatype,
                            'value': value,
                            'allocation': alloc,
                        }
                aaobj, created = AllocationAttribute.objects.get_or_create(**args)
                if created:
                    self.verbose_msg(options,
                            'Created AllocationAttribute {} with '
                            'value {} for Allocation {}'.format(aaobj, value, alloc),
                            1)
                else:
                    self.verbose_msg(options,
                            'AllocationAttribute {} with value {} '
                            'for Allocation {} already exists, not creating'.format(
                                aaobj, value, alloc),
                            2)
        return

    def handle(self, *args, **options):
        self.create_org_levels(options)
        self.create_orgs(options)
        self.create_users(options)
        self.create_resources(options)
        self.create_projects(options)
        self.create_allocations(options)
        return
