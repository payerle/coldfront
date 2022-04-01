import sys
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.test import TestCase

import coldfront.plugins.xdmod.utils as xdmod
import coldfront.plugins.slurm.utils as slurm

ATTRIBNAME_FOR_CACHED_VARS = 'coldfront_config_var_cache'

class ConfigChangingTestCase(TestCase):
    """For TestCases which need to change ColdFront config vars.

    This is an abstract base class, inheriting from Django TestCase
    for TestCases which need to temporarily modify Coldfront config
    variables.

    We provide a pair of helper methods, on of which will 
    cache the old value and set to a new value, and the other will
    restore the old value.  The values are cached in an instance
    variable (dict valued) of the ConfigChangingTestCase instance
    (named using the 'attribname_for_cached_vars' class variable
    for the instance variable name).

    """

    # Class variable specifying the name of the instance variable
    # holding the cache
    attribname_for_cached_vars=ATTRIBNAME_FOR_CACHED_VARS

    # Helper functions
    def get_coldfront_config_cache(self):
        """Returns the coldfront config cache dictionary.

        Will create an empty dictionary if needed.
        """
        attribname = ConfigChangingTestCase.attribname_for_cached_vars
        if not hasattr(self, attribname):
            setattr(self, attribname, {})
        cache = getattr(self, attribname)
        return cache
    
    def get_coldfront_package_from_string(self, pkgname):
        """Returns the ColdFront package from a string.

        Recognized strings are:
            slurm: Returns the package for coldfront.plugins.slurm.utils
            xdmod: Returns the package for coldfront.plugins.xdmod.utils
        Any other string will raise a ValueError
        """
        if pkgname == 'slurm':
            return slurm
        elif pkgname == 'xdmod':
            return xdmod
        else:
            raise ValueError('Expecting pkgname to be slurm or xdmod')
        return

    def set_and_cache_coldfront_config_variable(self, pkgname, varname, new):
        """Sets and caches a config variable from ColdFront.

        pkgname should be a string for the package the config variable
        is from.  See get_coldfront_package_from_string for list of
        allowed values.

        varname should be string with the name of the variable,
        e.g. SLURM_CLUSTER_ATTRIBUTE_NAME

        new should be the value to set the variable to.
        Return value is the previous value of the variable
        """

        # Get our package and ensure varname is found in it
        pkg = self.get_coldfront_package_from_string(pkgname)
        if not hasattr(pkg, varname):
            raise RuntimeError('Variable {} appears not to be in {}'.format(
                varname, pkgname))
        # And get the current value of the variable
        oldval = getattr(pkg,varname)

        # Get our cache
        main_cache = self.get_coldfront_config_cache()
        if pkgname in main_cache:
            pkg_cache = main_cache[pkgname]
        else:
            # Not found, create empty dict
            pkg_cache = {}
            main_cache[pkgname] = pkg_cache

        # Ensure we have not already cached a value for it
        if varname in pkg_cache:
            # We already have a value cached for varname
            # We only allow this if the current and cached values
            # are the same
            olderval = pkg_cache[varname]
            if olderval != oldval:
                # Values do not match --- error
                raise RuntimeError('Already have a cached version of {} '
                    'with value {}, cannot cache'.format(
                    varname))
        else:
            # Cache the current value
            pkg_cache[varname] = oldval

        # And set to new value
        setattr(pkg, varname, new)
        return oldval

    def restore_cached_coldfront_config_variable(self, pkgname, varname):
        """Restores a coldfront config variable from the cache.
        
        Restores a coldfront config variable as cached by
        set_and_cache_coldfront_config_variable

        pkgname should be a string for the package the config variable
        is from.  See get_coldfront_package_from_string for list of
        allowed values.

        varname should be string with the name of the variable

        We will raise a RuntimeError if variable was not previously
        cached.

        We return the cached value of the variable (as well as setting
        the variable back to the cached value and deleting the cache entry)
        """
        # Get our package
        pkg = self.get_coldfront_package_from_string(pkgname)

        # Get our cache
        main_cache = self.get_coldfront_config_cache()
        if pkgname in main_cache:
            pkg_cache = main_cache[pkgname]
        else:
            raise RuntimeError('Attempt to restore var {} in pkg {} '
                'from the cache, but not vars for pkg are cached'.format(
                    varname, pkgname))

        if varname in pkg_cache:
            # Restore cached value
            oldval = pkg_cache[varname]
            setattr(pkg, varname, oldval)
            del pkg_cache[varname]
        else:
            raise RuntimeError('Attempt to restore var {} in pkg {} '
                'from cache but no cached value found'.format(
                    varname, pkgname))
        return oldval

    def set_and_cache_coldfront_config_variables(self, varhash):
        """Calls set_and_cache_coldfront_config_variable for all vars in dict.

        This method will set a bunch of ColdFront configuration variables for
        different packages to new values, caching the old values for later
        restoration.

        The dictionary varhash should have keys representing ColdFront
        packages, e.g. slurm, xdmod.  See get_coldfront_package_from_string
        for list of allowed values.

        The value for each key is again a dictionary, this time keyed on the
        name of the variable to cache and set.  The value for the key is
        the new value to set the variable to.
        """
        for pkgname, pkghash in varhash.items():
            for varname, newval in pkghash.items():
                self.set_and_cache_coldfront_config_variable(
                        pkgname, varname, newval)
        return

    def restore_cached_coldfront_config_variables(self, varhash):
        """Calls restore_cached_coldfront_config_variable for all vars in varhash.

        This will restore the values for a bunch of ColdFront configuration
        variables from the values in the cache.  I.e., it reverts the action
        of set_and_cache_coldfront_config_variable(s).

        The dictionary varhash has the same format as for the method
        set_and_cache_coldfront_config_variables, although for this method
        the actual values in the inner hash are ignored.
        """
        for pkgname, pkghash in varhash.items():
            for varname in pkghash:
                self.restore_cached_coldfront_config_variable(
                        pkgname, varname)
        return

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
from coldfront.core.allocation.models import AttributeType as AAttributeType

from coldfront.core.field_of_science.models import (
        FieldOfScience,
        )
                                        
#                                        
#DEFAULT_FIXTURE_NAME='organization_test_data.json'
#DEFAULT_FIXTURE_DIR='./coldfront/coldfront/core/utils/fixtures'
#
#
#
#class TestFixtureBuilderCommand(BaseCommand):
#    """Base class for commands to build fixtures for tests.
#    """
#
#    help = 'Setup test data and make fixtures'
#
#    def verbose_msg(self, options, message, level=0):
#        """Print message if verbosity > level."""
#        verbosity = options['verbosity']
#        if verbosity > level:
#            label = 'DEBUG'
#            if level:
#                label = 'DEBUG{}'.format(level)
#            message.strip()
#            text = '[{}] {}\n'.format(label, message)
#            sys.stderr.write(text)
#        return
#
#    def create_organization_level_from_dict(self, ol_dict, options={}):
#        """Create an OrganizationLevel from data in ol_dict
#        
#        The dictionary ol_dict can contain the following fields
#            name: Name of the OrganizationLevel, required
#            level: level of the OrganizationLevel, required
#            parent: Name of parent OrganizationLevel.  Defaults to None
#
#        options is a dictionary controlling optional behavior. The
#        only key which is relevant is 'verbosity' which controls how
#        verbose the method is (it is passed to verbose_msg)
#        """
#        args = {}
#        args['name'] =  ol_dict['name']
#        args['level'] = ol_dict['level']
#        if 'parent' in ol_dict:
#            pname = rec['parent']
#            if pname is not None:
#                parent = OrganizationLevel.objects.get(name=pname)
#                args['parent'] = parent
#
#LEFT OFF HERE
#        obj, created = OrganizationLevel.objects.get_or_create(**args)
#    
#        for rec in orglevels:
#            args = {}
#            args['name'] = rec['name']
#            args['level'] = rec['level']
#            parent = None
#            if 'parent' in rec:
#                pname = rec['parent']
#                if pname is not None:
#            args['parent'] = parent
#
#            if created:
#                self.verbose_msg(options, 
#                        'Created OrganizationLevel {}'.format(obj),
#                        1)
#            else:
#                self.verbose_msg(options, 
#                        'OrganizationLevel {} already exists, not creating'.format(obj),
#                        2)
#        return
#
#    def create_orgs(self, options):
#        """Create Orgs for test data"""
#        self.verbose_msg(options, 'Creating Organizations as needed')
#        orgs = [
#                # University level
#                {   'code': 'Unknown',
#                    'organization_level': 'University',
#                    'parent': None,
#                    'shortname': 'Unknown',
#                    'longname': 'Container for Unknown organizations',
#                    'is_selectable_for_user': False,
#                    'is_selectable_for_project': False,
#                },
#                {   'code': 'UMD',
#                    'organization_level': 'University',
#                    'parent': None,
#                    'shortname': 'UMCP',
#                    'longname': 'University of Maryland',
#                    'is_selectable_for_user': False,
#                    'is_selectable_for_project': False,
#                },
#                {   'code': 'UMB',
#                    'organization_level': 'University',
#                    'parent': None,
#                    'shortname': 'UMD Baltimore',
#                    'longname': 'University of Maryland, Baltimore',
#                    'is_selectable_for_user': False,
#                    'is_selectable_for_project': False,
#                },
#                # College level - UMD
#                {   'code': 'CMNS',
#                    'organization_level': 'College',
#                    'parent': 'UMD',
#                    'shortname': 'CMNS',
#                    'longname': 'College of Computer, Mathematical, and Natural Sciences',
#                    'is_selectable_for_user': False,
#                    'is_selectable_for_project': False,
#                },
#                {   'code': 'ENGR',
#                    'organization_level': 'College',
#                    'parent': 'UMD',
#                    'shortname': 'Engineering',
#                    'longname': 'School of Engineering',
#                    'is_selectable_for_user': False,
#                    'is_selectable_for_project': False,
#                },
#                # Departmental level - UMD-CMNS
#                {   'code': 'ASTR',
#                    'organization_level': 'Department',
#                    'parent': 'UMD-CMNS',
#                    'shortname': 'Astronomy',
#                    'longname': 'Astronomy Department',
#                    'is_selectable_for_user': True,
#                    'is_selectable_for_project': True,
#                },
#                {   'code': 'PHYS',
#                    'organization_level': 'Department',
#                    'parent': 'UMD-CMNS',
#                    'shortname': 'Physics',
#                    'longname': 'Physics Department',
#                    'is_selectable_for_user': True,
#                    'is_selectable_for_project': True,
#                },
#                # Departmental level - UMD-ENGR
#                {   'code': 'ENAE',
#                    'organization_level': 'Department',
#                    'parent': 'UMD-ENGR',
#                    'shortname': 'Aeronautical Eng',
#                    'longname': 'Dept of Aeronautical Engineering',
#                    'is_selectable_for_user': True,
#                    'is_selectable_for_project': True,
#                },
#                {   'code': 'ENMA',
#                    'organization_level': 'Department',
#                    'parent': 'UMD-ENGR',
#                    'shortname': 'Materials Eng',
#                    'longname': 'Dept of Materials Engineering',
#                    'is_selectable_for_user': True,
#                    'is_selectable_for_project': True,
#                },
#                # College level - UMB
#                {   'code': 'SoM',
#                    'organization_level': 'College',
#                    'parent': 'UMB',
#                    'shortname': 'Medicine',
#                    'longname': 'School of Medicine',
#                    'is_selectable_for_user': False,
#                    'is_selectable_for_project': False,
#                },
#                {   'code': 'SoD',
#                    'organization_level': 'College',
#                    'parent': 'UMB',
#                    'shortname': 'Dentistry',
#                    'longname': 'School of Dentistry',
#                    'is_selectable_for_user': False,
#                    'is_selectable_for_project': False,
#                },
#                # Departmental level - UMB-SoM
#                {   'code': 'Psych',
#                    'organization_level': 'Department',
#                    'parent': 'UMB-SoM',
#                    'shortname': 'Psychiatry',
#                    'longname': 'Psychiatry Department',
#                    'is_selectable_for_user': True,
#                    'is_selectable_for_project': True,
#                },
#                {   'code': 'Surg',
#                    'organization_level': 'Department',
#                    'parent': 'UMB-SoM',
#                    'shortname': 'Surgery',
#                    'longname': 'Surgery Department',
#                    'is_selectable_for_user': True,
#                    'is_selectable_for_project': True,
#                },
#                # Departmental level - UMB-SoD
#                {   'code': 'NeuPain',
#                    'organization_level': 'Department',
#                    'parent': 'UMB-SoD',
#                    'shortname': 'Neural and Pain',
#                    'longname': 'Department of Neural and Pain Sciences',
#                    'is_selectable_for_user': True,
#                    'is_selectable_for_project': True,
#                },
#                {   'code': 'Perio',
#                    'organization_level': 'Department',
#                    'parent': 'UMB-SoD',
#                    'shortname': 'Periodontics',
#                    'longname': 'Division of Periodontics',
#                    'is_selectable_for_user': True,
#                    'is_selectable_for_project': True,
#                },
#            ]
#                    
#        for rec in orgs:
#            args = {}
#            args['code'] = rec['code']
#
#            if 'shortname' in rec:
#                args['shortname'] = rec['shortname']
#            if 'longname' in rec:
#                args['longname'] = rec['longname']
#            if 'is_selectable_for_user' in rec:
#                args['is_selectable_for_user'] = rec['is_selectable_for_user']
#            if 'is_selectable_for_project' in rec:
#                args['is_selectable_for_project'] = rec['is_selectable_for_project']
#
#            olevname = rec['organization_level']
#            olev = OrganizationLevel.objects.get(name=olevname)
#            args['organization_level'] = olev
#
#            pname = rec['parent']
#            if pname is None:
#                parent = None
#            else:
#                parent = Organization.get_organization_by_fullcode(pname)
#                args['parent'] = parent
#
#            obj, created, changed = Organization.create_or_update_organization(
#                    args)
#            if created:
#                self.verbose_msg(options, 
#                        'Created Organization {}'.format(obj),
#                        1)
#            else:
#                self.verbose_msg(options, 
#                        'Organization {} already exists, not creating'.format(obj),
#                        2)
#        return
#
#    def create_users(self, options):
#        """Create Users for test data"""
#        self.verbose_msg(options, 'Creating Users as needed')
#        users = [
#                # Users
#                {   'username': 'newton',
#                    'first_name': 'Isaac',
#                    'last_name': 'Newton',
#                    'primary_department': 'UMD-CMNS-PHYS',
#                    'is_pi': False,
#                },
#                {   'username': 'einstein',
#                    'first_name': 'Albert',
#                    'last_name': 'Einstein',
#                    'primary_department': 'UMD-CMNS-PHYS',
#                    'is_pi': True,
#                },
#                {   'username': 'freud',
#                    'first_name': 'Sigmund',
#                    'last_name': 'Freud',
#                    'primary_department': 'UMB-SoM-Psych',
#                    'is_pi': True,
#                },
#                {   'username': 'hawkeye',
#                    'first_name': 'Benjamin',
#                    'last_name': 'Pierce',
#                    'primary_department': 'UMB-SoM-Surg',
#                    'is_pi': True,
#                },
#                {   'username': 'orville',
#                    'first_name': 'Orville',
#                    'last_name': 'Wright',
#                    'primary_department': 'UMD-ENGR-ENAE',
#                    'is_pi': True,
#                },
#                {   'username': 'wilbur',
#                    'first_name': 'Wilbur',
#                    'last_name': 'Wright',
#                    'primary_department': 'UMD-ENGR-ENAE',
#                    'is_pi': False,
#                },
#            ]
#
#
#        for urec in users:
#            args = {}
#            uname = urec['username']
#            args['username'] = uname
#            lname = urec['last_name']
#            args['last_name'] = lname
#            fname = urec['first_name']
#            args['first_name'] = fname
#            if 'email' in urec:
#                email = urec['email']
#            else:
#                email = '{}@example.com'.format(uname)
#            args['email'] = email
#            user, created = User.objects.get_or_create(**args)
#            if created:
#                self.verbose_msg(options, 'Created User {} ({} {})'.format(
#                    user.username, fname, lname), 1)
#            else:
#                self.verbose_msg(options, 
#                        'User {} ({} {}) already exists, not creating'.format(
#                            user.username,
#                            fname,
#                            lname), 2)
#            
#            args = {    'user': user}
#            if 'primary_organization' in urec:
#                args['primary_organization'] = urec['primary_organization']
#            if 'ispi' in urec:
#                args['is_pi'] = urec['is_pi']
#            if 'additional_organizations' in urec:
#                args['additional_organizations'] = urec['additional_organizations']
#
#            # And generate UserProfile if needed
#            qset = UserProfile.objects.filter(user=user)
#            if qset:
#                created = False
#                changed = False
#                obj = qset[0]
#                if 'is_pi' in args:
#                    if obj.is_pi != args['is_pi']:
#                        obj.is_pi = args['ispi']
#                        changed = True
#                if 'primary_organization' in args:
#                    if obj.primary_organization != args['primary_organization']:
#                        obj.primary_organization = (
#                                args['primary_organization'].pk )
#                        changed = True
#                if 'additional_organizations' in args:
#                    if obj.additional_organizations != args['additional_organizations']:
#                        obj.additional_organizations = args['additional_organizations']
#                        changed = True
#
#                if changed:
#                    obj.save()
#            else:
#                created = True
#                obj = UserProfile.objects.get_or_create(args)
#
#            if created:
#                self.verbose_msg(options,
#                        'Created UserProfile for {}'.format(uname),
#                        1)
#            else:
#                self.verbose_msg(options, 
#                        'UserProfile for  {} already exists, not creating'.format(
#                            uname), 2)
#
#        return
#
#    def create_resources(self, options):
#        """Create Resources for test data"""
#        self.verbose_msg(options, 'Creating Resources as needed')
#        resources = [
#                { 
#                    'name': 'University HPC',
#                    'description': 'Main University HPC',
#                    'is_available': True,
#                    'is_public': True,
#                    'is_allocatable': True,
#                    'requires_payment': False,
#                    'parent_resource': None,
#                    'resource_type': 'Cluster',
#                    'resource_attributes': [
#                        {   'resource_attribute_type': 'slurm_cluster',
#                            'value': 'mainhpc',
#                        },
#                    ],
#                },
#            ]
#
#        for rec in resources:
#            args = {}
#            name = rec['name']
#            args['name'] = name
#
#            restype = rec['resource_type']
#            rtype = ResourceType.objects.get(name=restype)
#            args['resource_type'] = rtype
#
#            if 'description' in rec:
#                desc = rec['description']
#            else:
#                desc = name
#            args['description'] = desc
#
#            if 'is_available' in rec:
#                args['is_available'] = rec['is_available']
#            if 'is_public' in rec:
#                args['is_public'] = rec['is_public']
#            if 'is_allocatable' in rec:
#                args['is_allocatable'] = rec['is_allocatable']
#            if 'requires_payment' in rec:
#                args['requires_payment'] = rec['requires_payment']
#
#            if 'parent_resource' in rec:
#                parent_resource = rec['parent_resource']
#                if parent_resource is not None:
#                    parent = Resource.objects.get(name=parent_resource)
#                    args['parent'] = parent
#
#            if 'resource_attributes' in rec:
#                rattribs = rec['resource_attributes']
#            else:
#                rattribs = []
#
#            res, created = Resource.objects.get_or_create(**args)
#            if created:
#                self.verbose_msg(options, 
#                        'Created Resource {}'.format(res), 1)
#            else:
#                self.verbose_msg(options,
#                        'Resource {} already exists, not creating'.format(res),
#                        2)
#
#            # And create and needed resource_attributes
#            for rarec in rattribs:
#                ratname = rarec['resource_attribute_type']
#                ratype = ResourceAttributeType.objects.get(name=ratname)
#                value = rarec['value']
#                args = { 
#                        'resource_attribute_type': ratype,
#                        'value': value,
#                        'resource': res,
#                        }
#                raobj, created = ResourceAttribute.objects.get_or_create(**args)
#                if created:
#                    self.verbose_msg(options,
#                            'Created ResourceAttribute {} with '
#                            'value {} for Resource {}'.format(raobj, value, res),
#                            1)
#                else:
#                    self.verbose_msg(options,
#                            'ResourceAttribute {} with value {} '
#                            'for Resource {} already exists, not creating'.format(
#                                raobj, value, res),
#                            2)
#
#        return
#
#    def create_projects(self, options):
#        """Create Projects for test data"""
#        self.verbose_msg(options, 'Creating Projects as needed')
#        projects = [
#                { 
#                    'title': 'Gravitational Studies',
#                    'description': 'Study of Gravity',
#                    'pi_username': 'einstein',
#                    'field_of_science': 'Gravitational Physics',
#                    'force_review': False,
#                    'requires_review': True,
#                    'primary_organization': 'UMD-CMNS-PHYS',
#                    'additional_organizations': [],
#                    'users':
#                        [   'newton',
#                        ],
#                    'managers':
#                        [   'einstein',
#                        ]
#                },
#                { 
#                    'title': 'Hyposonic Flight',
#                    'description': 'Study of Flight at very low speeds',
#                    'pi_username': 'orville',
#                    'field_of_science': 'Other',
#                    'force_review': False,
#                    'requires_review': True,
#                    'primary_organization': 'UMD-ENGR-ENAE',
#                    'additional_organizations': [],
#                    'users':
#                        [   'wilbur',
#                        ],
#                    'managers':
#                        [   'orville',
#                        ]
#                },
#                { 
#                    'title': 'Artificial Id',
#                    'description': 'Attempts to build artificial intelligence with ego and id',
#                    'pi_username': 'freud',
#                    'field_of_science': 'Information, Robotics, and Intelligent Systems',
#                    'force_review': False,
#                    'requires_review': True,
#                    'primary_organization': 'UMB-SoM-Psych',
#                    'additional_organizations': [],
#                },
#                { 
#                    'title': 'Meatball Surgery',
#                    'description': 'Surgery under battlefield conditions',
#                    'pi_username': 'hawkeye',
#                    'field_of_science': 'Physiology and Behavior',
#                    'force_review': False,
#                    'requires_review': True,
#                    'primary_organization': 'UMB-SoM-Surg',
#                    'additional_organizations': [],
#                },
#
#            ]
#
#        active_status = None
#        for rec in projects:
#            args = {}
#            title = rec['title']
#            args['title'] = title
#
#            if 'pi_username' in rec:
#                pi_username = rec['pi_username']
#                qset = User.objects.filter(username=pi_username)
#                if qset:
#                    tmp = qset[0]
#                pi = User.objects.get(username=pi_username)
#                args['pi'] = pi
#
#            if 'description' in rec:
#                desc = rec['description']
#                args['description'] = desc
#
#            if 'status' in rec:
#                status = ProjectStatusChoice.objects.get(name=rec['status'])
#                args['status'] = status
#            else:
#                # Default to 'Active'
#                if active_status is None:
#                    active_status = ProjectStatusChoice.objects.get(
#                            name='Active')
#                args['status'] = active_status
#
#            if 'field_of_science' in rec:
#                fosname = rec['field_of_science']
#                fos = FieldOfScience.objects.get(description=fosname)
#                args['field_of_science'] = fos
#
#            if 'force_review' in rec:
#                args['force_review'] = rec['force_review']
#            if 'requires_review' in rec:
#                args['requires_review'] = rec['requires_review']
#
#            if 'primary_organization' in rec:
#                porg = Organization.get_organization_by_fullcode(
#                        rec['primary_organization'])
#                args['primary_organization'] = porg
#
#            if 'additional_organziations' in rec:
#                aorgs = rec['additional_organizations']
#                addorgs = []
#                for aorgcode in aorgs:
#                    aorg = Organization.get_organization_by_fullcode(aorgcode)
#                    addorgs.append(aorg)
#                args['additional_organizations'] = addorgs
#
#            obj, created = Project.objects.get_or_create(**args)
#            if created:
#                self.verbose_msg(options, 
#                        'Created Project {}'.format(obj), 1)
#            else:
#                self.verbose_msg(options,
#                        'Project {} already exists, not creating'.format(obj),
#                        2)
#
#            # And create project users
#            managers = []
#            role = ProjectUserRoleChoice.objects.get(name='Manager')
#            status = ProjectUserStatusChoice.objects.get(name='Active')
#            if 'managers' in rec:
#                mgrs = rec['managers']
#                for mgr in mgrs:
#                    user = User.objects.get(username=mgr)
#                    managers.append(user)
#            else:
#                managers = [ pi ]
#            for user in managers:
#                args = {
#                        'user': user,
#                        'project': obj,
#                        'role': role,
#                        'status': status,
#                        'enable_notifications': True,
#                    }
#                puser, created = ProjectUser.objects.get_or_create(**args)
#                if created:
#                    self.verbose_msg(options, 
#                            'Added ProjUser {} to Project {} as manager'.format(
#                                puser, obj), 1)
#                else:
#                    self.verbose_msg(options,
#                            'ProjectUser {} already in Project {}, not creating'.format(
#                                puser, obj), 2)
#
#            users = []
#            role = ProjectUserRoleChoice.objects.get(name='User')
#            if 'users' in rec:
#                usrs = rec['users']
#                for usr in usrs:
#                    user = User.objects.get(username=usr)
#                    users.append(user)
#                for user in users:
#                    args = {
#                            'user': user,
#                            'project': obj,
#                            'role': role,
#                            'status': status,
#                            'enable_notifications': True,
#                        }
#                    puser, created = ProjectUser.objects.get_or_create(**args)
#                    if created:
#                        self.verbose_msg(options, 
#                                'Added ProjUser {} to Project {} as user'.format(
#                                    puser, obj), 1)
#                    else:
#                        self.verbose_msg(options,
#                                'ProjectUser {} already in Project {}, not creating'.format(
#                                    puser, obj), 2)
#
#        return
#
#    def create_allocation_attribute_types(self, options):
#        """Create AllocationAttributeTypes for test data"""
#        self.verbose_msg(options, 'Creating AllocationAttributeTypes as needed')
#        aatypes = [
#                { 
#                    'name': 'slurm_account_name',
#                    'attribute_type_name': 'Text',
#                    'has_usage': False,
#                    'is_required': False,
#                    'is_unique': False,
#                    'is_private': False,
#                },
#                { 
#                    'name': 'slurm_specs',
#                    #'attribute_type_name': 'Text',
#                    #'has_usage': False,
#                    #'is_required': False,
#                    #'is_unique': False,
#                    #'is_private': False,
#                },
#                { 
#                    'name': 'slurm_user_specs',
#                    #'attribute_type_name': 'Text',
#                    #'has_usage': False,
#                    #'is_required': False,
#                    #'is_unique': False,
#                    #'is_private': False,
#                },
#                { 
#                    'name': 'xdmod_allocation_code',
#                    #'attribute_type_name': 'Text',
#                    #'has_usage': False,
#                    #'is_required': False,
#                    #'is_unique': False,
#                    #'is_private': False,
#                },
#                { 
#                    'name': 'xdmod_allocation_name',
#                    #'attribute_type_name': 'Text',
#                    #'has_usage': False,
#                    #'is_required': False,
#                    #'is_unique': False,
#                    #'is_private': False,
#                },
#                { 
#                    'name': 'xdmod_project_code',
#                    #'attribute_type_name': 'Text',
#                    #'has_usage': False,
#                    #'is_required': False,
#                    #'is_unique': False,
#                    #'is_private': False,
#                },
#            ]
#        # Cache atypes
#        atype_by_name = {}
#
#        for rec in aatypes:
#            args = {}
#
#            # Name is required
#            name = rec['name']
#            args['name'] = name
#
#            # Default attribute_type_name to 'Text', and
#            # cache the AttributeTypes
#            if 'attribute_type_name' in rec:
#                atype_name = rec['attribute_type_name']
#            else:
#                atype_name = 'Text'
#            if atype_name in atype_by_name:
#                # Use cached value
#                atype = atype_by_name[atype_name]
#            else:
#                atype = AAttributeType.objects.get(name=atype_name)
#                atype_by_name[atype_name]=atype
#            args['attribute_type'] = atype
#
#            # The model defaults all of the following, so optional
#            for key in ('has_usage', 'is_required', 'is_unique', 'is_private'):
#                if key in rec:
#                    args[key] = rec[key]
#
#            aatype, created = AllocationAttributeType.objects.get_or_create(**args)
#
#            if created:
#                self.verbose_msg(options, 
#                        'Created AllocationAttributeType {}'.format(
#                            aatype.name), 1)
#            else:
#                self.verbose_msg(options,
#                        'AllocationAttributeType {} already exists, '
#                        'not creating'.format(aatype.name), 2)
#        return
#
#    def create_allocations(self, options):
#        """Create Allocations for test data"""
#        self.verbose_msg(options, 'Creating Allocations as needed')
#        allocations = [
#                { 
#                    'description': 'einstein-alloc',
#                    'project': 'Gravitational Studies',
#                    'resources': ['University HPC' ],
#                    'justification': 'Must warp space-time',
#                    # 'status': 
#                    # 'quantity':
#                    # 'is-locked':
#                    # 'users':
#                    'allocation_attributes': [
#                        {   'allocation_attribute_type': 'slurm_account_name',
#                            'value': 'einstein-alloc',
#                        },
#                    ],
#
#                },
#                { 
#                    'description': 'wright-alloc',
#                    'project': 'Hyposonic Flight',
#                    'resources': ['University HPC' ],
#                    'justification': 'I need CPU',
#                    # 'status': 
#                    # 'quantity':
#                    # 'is-locked':
#                    # 'users':
#                    'allocation_attributes': [
#                        {   'allocation_attribute_type': 'slurm_account_name',
#                            'value': 'wright-alloc',
#                        },
#                        {   'allocation_attribute_type': 'xdmod_project_code',
#                            'value': 'wright-proj',
#                        },
#                        {   'allocation_attribute_type': 'xdmod_allocation_code',
#                            'value': 'hyposonicflight',
#                        },
#                    ],
#
#                },
#                { 
#                    'description': 'wilbur-alloc',
#                    'project': 'Hyposonic Flight',
#                    'resources': ['University HPC' ],
#                    'justification': 'Wilbur needs more CPU',
#                    # 'status': 
#                    # 'quantity':
#                    # 'is-locked':
#                    'users': [ 'wilbur' ],
#                    'allocation_attributes': [
#                        {   'allocation_attribute_type': 'slurm_account_name',
#                            'value': 'wilbur-alloc',
#                        },
#                        {   'allocation_attribute_type': 'xdmod_project_code',
#                            'value': 'wilbur-proj',
#                        },
#                        {   'allocation_attribute_type': 'xdmod_allocation_code',
#                            'value': 'hyposonicflight',
#                        },
#                    ],
#
#                },
#                { 
#                    'description': 'orville-alloc',
#                    'project': 'Hyposonic Flight',
#                    'resources': ['University HPC' ],
#                    'justification': 'Orville needs more CPU',
#                    # 'status': 
#                    # 'quantity':
#                    # 'is-locked':
#                    'users': [ 'orville' ],
#                    'allocation_attributes': [
#                        {   'allocation_attribute_type': 'slurm_account_name',
#                            'value': 'orville-alloc',
#                        },
#                        {   'allocation_attribute_type': 'xdmod_project_code',
#                            'value': 'orville-proj',
#                        },
#                        {   'allocation_attribute_type': 'xdmod_allocation_name',
#                            'value': 'Orville Wright allocation',
#                        },
#                    ],
#
#                },
#                { 
#                    'description': 'freud-alloc',
#                    'project': 'Artificial Id',
#                    'resources': ['University HPC' ],
#                    # 'status': 
#                    # 'quantity':
#                    # 'justification': 
#                    # 'is-locked':
#                    # 'users':
#                    'allocation_attributes': [
#                        {   'allocation_attribute_type': 'slurm_account_name',
#                            'value': 'freud-alloc',
#                        },
#                    ],
#
#                },
#                { 
#                    'description': 'hawkeye-alloc',
#                    'project': 'Meatball Surgery',
#                    'resources': ['University HPC' ],
#                    # 'status': 
#                    # 'quantity':
#                    # 'justification': 
#                    # 'is-locked':
#                    # 'users':
#                    'allocation_attributes': [
#                        {   'allocation_attribute_type': 'slurm_account_name',
#                            'value': 'hawkeye-alloc',
#                        },
#                    ],
#
#                },
#            ]
#
#        for rec in allocations:
#            args = {}
#
#            pname = rec['project']
#            if pname is not None:
#                try:
#                    proj = Project.objects.get(title=pname)
#                except Exception as exc:
#                    sys.stderr.write('[ERROR] No project named {} found\n'.format(
#                        pname))
#                    raise exc
#                args['project'] = proj
#
#            for field in ('quantity', 'is_locked', 'justification', 'description'):
#                if field in rec:
#                    args[field] = rec[field]
#
#            if 'status' in rec:
#                status_name = rec['status']
#            else:
#                status_name = 'Active'
#
#            status = AllocationStatusChoice.objects.get(name=status_name)
#            args['status'] = status
#
#            alloc, created = Allocation.objects.get_or_create(**args)
#
#            if created:
#                self.verbose_msg(options, 
#                        'Created Allocation {}'.format(alloc.description), 1)
#            else:
#                self.verbose_msg(options,
#                        'Allocation {} already exists, not creating'.format(
#                            alloc.description), 2)
#
#            # Add Resources to Allocation
#            resources = []
#            if 'resources' in rec:
#                rsrcs = rec['resources']
#                for rsrc in rsrcs:
#                    resource = Resource.objects.get(name=rsrc)
#                    resources.append(resource)
#            for resource in resources:
#                alloc.resources.add(resource)
#
#            # And create allocation users
#            users = None
#            if 'users' in rec:
#                unames = rec['users']
#                users = []
#                for uname in unames:
#                    user = User.objects.get(username=uname)
#                    users.append(user)
#            else:
#                # Default to active all ProjectUsers for this Project
#                pusers = ProjectUser.objects.filter(
#                        project__title=pname,
#                        status__name='Active')
#                users = [ x.user for x in pusers ]
#            status = AllocationUserStatusChoice.objects.get(name='Active')
#            for user in users:
#                args={
#                        'status': status,
#                        'allocation': alloc,
#                        'user': user,
#                        }
#                obj, created = AllocationUser.objects.get_or_create(**args)
#                if created:
#                    self.verbose_msg(options,
#                            'Created AllocationUser {} for Alloc {}'.format(
#                                obj, alloc), 1)
#                else:
#                    self.verbose_msg(options,
#                            'AllocationUser {} for Alloc {} already exists'.format(
#                                obj, alloc), 2)
#
#            # And add allocation attributes
#            aattribs = None
#            if 'allocation_attributes' in rec:
#                aattribs = rec['allocation_attributes']
#                for aarec in aattribs:
#                    aatname = aarec['allocation_attribute_type']
#                    aatype = AllocationAttributeType.objects.get(name=aatname)
#                    value = aarec['value']
#                    args = {
#                            'allocation_attribute_type': aatype,
#                            'value': value,
#                            'allocation': alloc,
#                        }
#                    aaobj, created = AllocationAttribute.objects.get_or_create(**args)
#                    if created:
#                        self.verbose_msg(options,
#                                'Created AllocationAttribute {} with '
#                                'value {} for Allocation {}'.format(aaobj, value, alloc),
#                                1)
#                    else: #if created
#                        self.verbose_msg(options,
#                                'AllocationAttribute {} with value {} '
#                                'for Allocation {} already exists, not creating'.format(
#                                    aaobj, value, alloc),
#                                2)
#                    #end if created
#                #end for aarec in aattribs:
#        return
#
#    def add_arguments(self, parser):
#
#        parser.add_argument('--fixture', 
#                help='Create a fixture',
#                action='store_true',
#                default=None)
#        parser.add_argument('--outfile', '--file', '-f',
#                help='Specify name to use for the fixture.  Implies --fixture if given; '
#                    'Defaults to {} if --fixture given'.format(DEFAULT_FIXTURE_NAME),
#                action='store',
#                default=None)
#        parser.add_argument('--directory','--dir', '-d',
#                help='Directory in which to store fixtures',
#                action='store',
#                default=DEFAULT_FIXTURE_DIR)
#        parser.add_argument('--force', '-F',
#                help='FORCE flag.  If set, allows clobbering of an '
#                    'existing fixture file',
#                action='store_true')
#        return
#
#    def handle(self, *args, **options):
#        outfile = options['outfile']
#        fixture = options['fixture']
#
#        # If outfile was set, then --fixture is implied
#        if outfile is not None:
#            # Outfile was given, this implies fixture
#            if fixture is None:
#                fixture = True
#            elif not fixture:
#                raise CommandError('--outfile given but fixture set to false, not allowed')
#
#        # If --fixture given, then default outfile
#        if fixture:
#            if outfile is None:
#                outfile = DEFAULT_FIXTURE_NAME
#
#        fixture_dir = options['directory']
#        FORCE = None
#        if 'force' in options:
#            FORCE = options['force']
#
#        # Verify fixture_dir exists and fixture is not being clobber
#        outfile_fq = None
#        if fixture:
#            outfile_fq = '{}/{}'.format(fixture_dir, outfile)
#            if not os.path.isdir(fixture_dir):
#                raise CommandError('Fixture directory {} does not exist'.format(
#                    fixture_dir))
#            if os.path.isfile(outfile_fq):
#                if not FORCE:
#                    raise CommandError('Fixture file {} already exists, '
#                            'refusing to clobber w/out force flag.'.format(
#                                outfile_fq))
#
#        self.create_org_levels(options)
#        self.create_orgs(options)
#        self.create_users(options)
#        self.create_resources(options)
#        self.create_projects(options)
#        self.create_allocation_attribute_types(options)
#        self.create_allocations(options)
#
#        if outfile_fq is not None:
#            call_command(
#                    "dumpdata", 
#                    format="json", 
#                    indent=2,
#                    exclude=[ "publication.PublicationSource" ],
#                    output=outfile_fq,
#                    )
#        return
