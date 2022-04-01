# Script to test OrganizationLevel methods
# including:
#   validate_orglevel_hierarchy
#   the integrity checks in clean(), etc.
#   the add_organization_level and delete_organization_level helper methods

import sys

from django.core.exceptions import ValidationError 
from django.db.models import ProtectedError
from django.test import TestCase

from coldfront.core.organization.models import (
        OrganizationLevel,
        Organization,
        )

EXPECTED_BASE_ORGLEVEL_HIERARCHY=[
    {   'name': 'University',
        'level': 40,
        'parent': None,
        'export_to_xdmod': True,
    },
    {   'name': 'College',
        'level': 30,
        'parent': 'University',
        'export_to_xdmod': True,

    },
    {   'name': 'Department',
        'level': 20,
        'parent': 'College',
        'export_to_xdmod': True,
    },
]

NEW_ORGLEVEL_LEAF={
        'name': 'ResearchGroup',
        'level': 10,
        'parent': 'Department',
        'export_to_xdmod': True,
    }

NEW_ORGLEVEL_BADLEAF1={
        'name': 'ResearchGroup',
        'level': 25,
        'parent': 'Department',
        'export_to_xdmod': True,
    }

NEW_ORGLEVEL_ROOT={
        'name': 'Country',
        'level': 50,
        'parent': None,
        'export_to_xdmod': True,
    }

NEW_ORGLEVEL_MIDDLE={
        'name': 'Center',
        'level': 25,
        'parent': 'College',
        'export_to_xdmod': True,
    }

class OrganizationLevelTest(TestCase):
    fixtures = ['organization_test_data.json']

    # Helper functions
    def orglevel_to_dict(self, orglevel):
        """Convert an OrgLevel to a dict"""
        retval = {
                'name': orglevel.name,
                'level': orglevel.level,
                'export_to_xdmod': orglevel.export_to_xdmod,
           }
        if orglevel.parent is None:
            retval['parent'] = None
        else:
            retval['parent'] = orglevel.parent.name
        return retval

    def orglevels_to_dicts(self, orglevels):
        """Run orglevel_to_dict on a list of orglevels"""
        retval = []
        for orglevel in orglevels:
            tmp = self.orglevel_to_dict(orglevel)
            retval.append(tmp)
        return retval

    def dump_orglevel(self, orglevel):
        """For debugging: dumps an OrganizationLevel instance to stderr"""
        name = orglevel.name
        level = orglevel.level
        parent = orglevel.parent
        pname = '<None>'
        if parent is not None:
            pname = parent.name
        xport = orglevel.export_to_xdmod
        sys.stderr.write('[DEBUG] OrgLevel={}:{} [parent={}] (xport={})\n'.format(
            name, level, pname, xport))
        return

    def dump_orglevels(self, orglevels):
        """For debugging: dumps a list of  OrganizationLevels to stderr"""
        for orglevel in orglevels:
            self.dump_orglevel(orglevel)
        return

    ########################################################################
    #                       Tests
    ########################################################################

    def test_orglevel_validate_succeeds(self):
        """Test that validate_orglevel_hierarchy succeeds"""
        try:
            OrganizationLevel.validate_orglevel_hierarchy()
        except Exception as exc:
            self.fail('validate_orglevel_hierarchy raised exception: {}'.format(
                exc))
        return

    def test_orglevel_hierarchy_list(self):
        """Test that we get our expected orglevel hierarchy list"""
        hlist = OrganizationLevel.generate_orglevel_hierarchy_list()
        got = self.orglevels_to_dicts(hlist)
        expected = list(EXPECTED_BASE_ORGLEVEL_HIERARCHY)
        self.assertEqual(got, expected)
        return

    def test_orglevel_add_delete_leaf_tier(self):
        """Test that we can successfully add and delete a leaf orglevel"""

        parent_oname = NEW_ORGLEVEL_LEAF['parent']
        parent_olev = OrganizationLevel.objects.get(name=parent_oname)
        new_args = dict(NEW_ORGLEVEL_LEAF)
        del new_args['parent']
        new_args['parent'] = parent_olev

        try:
            # Add OrgLevel
            newolev = OrganizationLevel.objects.create(**new_args)
        except Exception as exc:
            self.fail('exception raised on adding new leaf OrgLevel: {}'.format(
                exc))

        # Make sure OrgLevel hierarchy is correct
        hlist = OrganizationLevel.generate_orglevel_hierarchy_list()
        got = self.orglevels_to_dicts(hlist)
        expected = list(EXPECTED_BASE_ORGLEVEL_HIERARCHY)
        expected.append(NEW_ORGLEVEL_LEAF)
        self.assertEqual(got, expected)

        try:
            # Delete OrgLevel
            newolev.delete()
        except Exception as exc:
            self.fail('exception raised on deleting new leaf OrgLevel: {}'.format(
                exc))

        # Make sure OrgLevel hierarchy is correct
        hlist = OrganizationLevel.generate_orglevel_hierarchy_list()
        got = self.orglevels_to_dicts(hlist)
        expected = list(EXPECTED_BASE_ORGLEVEL_HIERARCHY)
        self.assertEqual(got, expected)

        return

    def test_orglevel_dont_naive_add_root_tier(self):
        """Test that we cannot naively add a root tier"""
        # Add a root OrgLevel tier, we expect to fail
        new_args = dict(NEW_ORGLEVEL_ROOT)
        newolev = None
        with self.assertRaises(ValidationError) as cm:
            newolev = OrganizationLevel.objects.create(**new_args)

        if newolev is not None:
            # Cleanup in case did not raise exception
            newolev.delete()

#        exc = cm.exception
#        sys.stderr.write('[TPTEST] naive_add_root: exc={}: {}\n'.format(
#            type(exc), exc))
        return

    def test_orglevel_dont_naive_delete_root_tier(self):
        """Test that we cannot naively delete the root tier"""

        hlist = OrganizationLevel.generate_orglevel_hierarchy_list()
        oldroot = hlist[0]
        with self.assertRaises(ProtectedError) as cm:
            oldroot.delete()

        exc = cm.exception
        if not exc:
            sys.stderr.write(
                    '******************************\n'
                    '[FATAL] Deleted root orglevel tier\n'
                    'Subsequent tests likely to fail\n'
                    '******************************\n'
                    )
        return

    def test_orglevel_dont_naive_delete_middle_tier(self):
        """Test that we cannot naively delete the middle tier"""

        hlist = OrganizationLevel.generate_orglevel_hierarchy_list()
        middle = hlist[1]
        with self.assertRaises(ProtectedError) as cm:
            middle.delete()

        exc = cm.exception
        if not exc:
            sys.stderr.write(
                    '******************************\n'
                    '[FATAL] Deleted middle orglevel tier\n'
                    'Subsequent tests likely to fail\n'
                    '******************************\n'
                    )
        return

    def test_orglevel_dont_naive_delete_leaf_tier(self):
        """Test that we cannot naively delete the leaf tier"""

        hlist = OrganizationLevel.generate_orglevel_hierarchy_list()
        leaf = hlist[-1]
        with self.assertRaises(ProtectedError) as cm:
            leaf.delete()

        exc = cm.exception
        if not exc:
            sys.stderr.write(
                    '******************************\n'
                    '[FATAL] Deleted leaf orglevel tier\n'
                    'Subsequent tests likely to fail\n'
                    '******************************\n'
                    )
        return

    def test_orglevel_dont_naive_add_middle_tier(self):
        """Test that we cannot naively add a middle tier"""

        # Add a middle OrgLevel tier, we expect to fail
        new_args = dict(NEW_ORGLEVEL_MIDDLE)
        parent_oname = new_args['parent']
        del new_args['parent']

        parent_olev = OrganizationLevel.objects.get(name=parent_oname)
        new_args['parent'] = parent_olev
        newolev = None
        with self.assertRaises(ValidationError) as cm:
            newolev = OrganizationLevel.objects.create(**new_args)

        if newolev is not None:
            # Cleanup in case did not raise exception
            newolev.delete()

#        exc = cm.exception
#        sys.stderr.write('[TPTEST] naive_add_middle: exc={}: {}\n'.format(
#            type(exc), exc))
        return

    def test_orglevel_dont_naive_add_middle_tier2(self):
        """Test that we cannot naively add a middle tier even when checks disabled"""
        new_args = dict(NEW_ORGLEVEL_MIDDLE)
        parent_oname = new_args['parent']
        del new_args['parent']
        parent_olev = OrganizationLevel.objects.get(name=parent_oname)
        new_args['parent'] = parent_olev
        newolev = None

        # Force the addition of an invalid root tier
        OrganizationLevel.disable_validation_checks(True)
        with self.assertRaises(ValidationError) as cm:
            newolev = OrganizationLevel.objects.create(**new_args)
        OrganizationLevel.disable_validation_checks(False)

        # Cleanup
        if newolev:
            OrganizationLevel.disable_validation_checks(True)
            newolev.delete()
            OrganizationLevel.disable_validation_checks(False)

#        exc = cm.exception
#        sys.stderr.write('[TPTEST] naive_add_middle_tier2: exc={}: {}\n'.format(
#            type(exc), exc))
        return

    def test_orglevel_dont_naive_add_badleaf1_tier(self):
        """Test that we cannot naively add a bad leaf tier (1)"""

        # Add a bad leaf1 OrgLevel tier, we expect to fail
        new_args = dict(NEW_ORGLEVEL_BADLEAF1)
        parent_oname = new_args['parent']
        del new_args['parent']

        parent_olev = OrganizationLevel.objects.get(name=parent_oname)
        new_args['parent'] = parent_olev
        newolev = None
        with self.assertRaises(ValidationError) as cm:
            newolev = OrganizationLevel.objects.create(**new_args)

        if newolev is not None:
            # Cleanup in case did not raise exception
            newolev.delete()

#        exc = cm.exception
#        sys.stderr.write('[TPTEST] naive_add_middle: exc={}: {}\n'.format(
#            type(exc), exc))
        return


    def test_orglevel_add_delete_root_tier(self):
        """Test that we can successfully add/delete_organization_level for root orglevel"""

        # Find any Organizations at root level before we add new root
        hlist = OrganizationLevel.generate_orglevel_hierarchy_list()
        old_root_olev = hlist[0]
        old_root_orgs = Organization.objects.filter(
                organization_level=old_root_olev).order_by('pk')

        #parent_oname = NEW_ORGLEVEL_ROOT['parent']
        #parent_olev = OrganizationLevel.objects.get(name=parent_oname)
        new_args = dict(NEW_ORGLEVEL_ROOT)
        #del new_args['parent']
        #new_args['parent'] = parent_olev

        try:
            # Add OrgLevel
            newolev = OrganizationLevel.add_organization_level(**new_args)
        except Exception as exc:
            self.fail('exception raised on add_organization_level on new root OrgLevel: {}'.format(
                exc))

        # Make sure OrgLevel hierarchy is correct
        hlist = OrganizationLevel.generate_orglevel_hierarchy_list()
        got = self.orglevels_to_dicts(hlist)
        expected = list(EXPECTED_BASE_ORGLEVEL_HIERARCHY)
        # Replace old root in expected with a copy 
        expected[0] = dict(expected[0])
        # and change parent 
        expected[0]['parent'] = NEW_ORGLEVEL_ROOT['name']
        # And prepend new root
        expected.insert(0, NEW_ORGLEVEL_ROOT)
        self.assertEqual(got, expected)

        new_root_org = None
        if old_root_orgs:
            # Check that we have a new root level organization
            # (only happens if there was previously at least one root level org)
            qset = Organization.objects.filter(organization_level=newolev)
            self.assertEqual(len(qset), 1, msg='Expected a single root level Organization')
            new_root_org = qset[0]

            # And that children of this new root org are the old root orgs
            # We compare pk's of orgs as Orgs themselves have different parents
            new_subroot_orgs = Organization.objects.filter(
                    parent=new_root_org).order_by('pk')

            got = [ x.pk for x in new_subroot_orgs ]
            expected = [ x.pk for x in old_root_orgs ]
            self.assertEqual(got, expected, msg='Old root orgs now under new root org')

        # Delete the newly created root Organization
        if new_root_org is not None:
            # First we must delete the new root org and set old_root_orgs' parents to None
            #(only if previously had an root level org)
            try:
                Organization.disable_validation_checks(True)
                for org in new_subroot_orgs:
                    org.parent = None
                    org.save()
                new_root_org.delete()
                Organization.disable_validation_checks(False)
            except Exception as exc:
                self.fail('exception raised on deleting new placeholder '
                    'root Org: {}'.format(exc))

        # Delete the newly created root OrganizationLevel
        try:
            newolev.delete_organization_level()
        except Exception as exc:
            self.fail('exception raised on delete_organization_level for new root: {}'.format(
                exc))

        # Make sure OrgLevel hierarchy is correct
        hlist = OrganizationLevel.generate_orglevel_hierarchy_list()
        got = self.orglevels_to_dicts(hlist)
        expected = list(EXPECTED_BASE_ORGLEVEL_HIERARCHY)
        self.assertEqual(got, expected)

        return

    def test_orglevel_validate_fails_on_bad_root(self):
        """Test that validate_orglevel_hierarchy fails on invalid hierarchy (bad root)"""
        # Force the addition of an invalid root tier
        new_args = dict(NEW_ORGLEVEL_ROOT)
        newolev = None
        OrganizationLevel.disable_validation_checks(True)
        newolev = OrganizationLevel.objects.create(**new_args)
        OrganizationLevel.disable_validation_checks(False)

        with self.assertRaises(ValidationError) as cm:
            OrganizationLevel.validate_orglevel_hierarchy()

        # Cleanup
        if newolev:
            OrganizationLevel.disable_validation_checks(True)
            newolev.delete()
            OrganizationLevel.disable_validation_checks(False)

#        exc = cm.exception
#        sys.stderr.write('[TPTEST] validate_fails_on_bad_root: exc={}: {}\n'.format(
#            type(exc), exc))
        return

    def test_orglevel_validate_warns_if_checks_disabled(self):
        """Test that validate_orglevel_hierarchy warns on disable_validation_checks"""
        OrganizationLevel.disable_validation_checks(True)
        with self.assertWarns(Warning) as cm:
            OrganizationLevel.validate_orglevel_hierarchy()

        # Cleanup
        OrganizationLevel.disable_validation_checks(False)

#        exc = cm.warning
#        sys.stderr.write('[TPTEST] naive_orglevel_validate3: warning={}: {}\n'.format(
#            type(exc), exc))
        return

    def test_orglevel_validate_fails_on_bad_leaf(self):
        """Test that validate_orglevel_hierarchy fails on invalid hierarchy (bad leaf)"""
        # Force the addition of an invalid badleaf tier
        new_args = dict(NEW_ORGLEVEL_BADLEAF1)
        parent_oname = new_args['parent']
        del new_args['parent']

        parent_olev = OrganizationLevel.objects.get(name=parent_oname)
        new_args['parent'] = parent_olev
        newolev = None

        OrganizationLevel.disable_validation_checks(True)
        newolev = OrganizationLevel.objects.create(**new_args)
        OrganizationLevel.disable_validation_checks(False)

        with self.assertRaises(ValidationError) as cm:
            OrganizationLevel.validate_orglevel_hierarchy()

        # Cleanup
        if newolev:
            OrganizationLevel.disable_validation_checks(True)
            newolev.delete()
            OrganizationLevel.disable_validation_checks(False)

#        exc = cm.exception
#        sys.stderr.write('[TPTEST] validate_fails_on_bad_leaf exc={}: {}\n'.format(
#            type(exc), exc))
        return

