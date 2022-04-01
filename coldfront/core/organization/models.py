import sys
import logging
import warnings

from django.db import models
from model_utils.models import TimeStampedModel
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db.models import Q, Max

logger = logging.getLogger(__name__)

class OrganizationLevel(TimeStampedModel):
    """This defines the different organization levels.

    Each level has a name, level, and optionally a parent.  The level
    describes where in the hierarchy it is, the higher the value for
    level, the higher (more encompassing) the level.  E.g., an 
    academic setting might have levels defined by:
    40: University
    30: College 
    20: Department
    10: ResearchGroup

    The parent would be NULL for the highest level, and for other
    levels should reference the unique entry at the next highest level.
    """

    name = models.CharField(
            max_length=512, 
            null=True, 
            blank=False, 
            unique=True,
            help_text='The (unique) name of the OrganizationLevel',)
    level = models.IntegerField(
            null=False, 
            blank=False, 
            unique=True,
            help_text='The lower this value, the higher this type is in '
                'the organization.')
    parent = models.OneToOneField(
            'self', 
            on_delete=models.PROTECT,
            null=True, 
            blank=True,
            unique=True,
            help_text='The parent OrganizationLevel for this '
                'OrganizationLevel, or None for the root '
                'OrganizationLevel')
    export_to_xdmod = models.BooleanField(
            default=True,
            help_text='If set, this OrganizationLevel will be '
                'exported to Open XdMod')
    # Disable the validation constraints if true.
    # Intended for temporary use when adding/deleting OrgLevels (see
    # add_organization_level and delete_organization_level methods).
    # Always use accessor disable_validation_checks for getting/setting
    # to make it truly behave as class variable
    _disable_validation_checks=False

    def __str__(self):
        return self.name

    @classmethod
    def disable_validation_checks(cls, new=None):
        """Accessor/mutator for _disable_validation_checks class data member.

        Because of the 'magic' done by django with class variables of Models,
        we must always use the explicit class name when referring to the
        class variable, otherwise we can end up with instance-like copies.

        To better support this, always use this accessor/mutator for getting or
        setting the value.
        """
        if new is not None:
            OrganizationLevel._disable_validation_checks = new
        return OrganizationLevel._disable_validation_checks

    def clean(self):
        """Validation: ensure our parent has a higher level than us

        If we have a parent, make sure it has a higher level than us.
        If we do not have a parent, make sure there are no other rows
        in table. (UNIQUE on parent does not work, as SQL allows multiple
        rows with NULL for an UNIQUE field).

        These checks are ignored if disable_validation_checks is set; 
        this is intended for temporary use in add_organization_level
        and delete_organization_level methods.
        """
        # First, call base class's version
        super().clean()

        # Skip custom validation checks if disable_validation_checks
        if self.disable_validation_checks():
            return

        if self.parent:
            # Has a parent, make sure has higher level than us
            plevel = self.parent.level
            if plevel <= self.level:
                raise ValidationError( 'OrganizationLevel {}, level={} '
                    'has parent {} with lower level {}\n' .format(
                        self, 
                        self.level,
                        self.parent, 
                        plevel))
        else: #if self.parent
            # No parent
            # Are there any other OrganizationLevels
            qset = OrganizationLevel.objects.all()
            if qset:
                #Yes, make sure we are the highest level in table
                maxlevel = list(qset.aggregate(Max('level')).values())[0]
                if maxlevel > self.level:
                    raise ValidationError('OrganizationLevel {}, level={} '
                        'has no parent, but max level={}' .format(
                            self, self.level, maxlevel))
                # And that no other parent-less OrgLevels present
                qset2 = qset.filter(parent__isnull=True)
                if qset2:
                    tmp = [ x.name for x in qset ]
                    tmpstr = ', '.join(tmp)
                    raise ValidationError('OrganizationLevel {}, level={} '
                            'has no parent, but [{}] also parentless'.format(
                                self.name, self.level, tmpstr))
                #end if qset2
            #end if qset
        #end if self.parent
        return

    def save(self, *args, **kwargs):
        """Override save() to call full_clean first"""
        self.full_clean()
        return super(OrganizationLevel, self).save(*args, **kwargs)
                
    def update_orglevel_from_dict(self, new):
        """Updates OrganizationLevel to match dictionary.

        The fields of the invocant will be updated to match the
        fields of the dictionary new.  Fields not present in the
        dictionary new are ignored/left unchanged.

        Returns None if no fields have been changed, or a 
        dictionary with keys and values of fields which have been changed.
        """
        retval = {}
        for key, value in new.items():
            if key == 'name':
                if self.name != value:
                    self.name = value
                    retval['name'] = value
            elif key == 'level':
                if self.name != value:
                    self.level = value
                    retval['level'] = value
            elif key == 'parent':
                if self.parent != value:
                    self.parent = value.pk
                    retval['parent'] = value
            elif key == 'export_to_xdmod':
                if self.export_to_xdmod != value:
                    self.export_to_xdmod = value
                    retval['export_to_xdmod'] = value
            else:
                raise ValueError('No field {} for {}\n'.format(
                    key, self))

        if retval:
            self.save()
        else:
            retval = None
        return retval

    @classmethod
    def create_or_update_orglevel(self, new):
        """Creates or Updates OrganizationLevel as needed.

        This method will check if an OrganizationLevel with name or
        level as given by fields of new.  If no such OrganizationLevel
        was found, a new OrganizationLevel is created using the arguments
        from the dictionary new.

        If such an OrganizationLevel is found, it is updated to match
        the fields listed in new.  Any fields not present as keys to new
        will not be updated.

        Returns a triplet consisting of the OrganizationLevel found or 
        created, a boolean indicating if a new object was created, and a 
        (possibly empty) dictionary with the key/values of the fields 
        which have been changed.
        """
        created = False
        changed = {}
        if 'name' in new:
            name = new['name']
        else:
            name = None

        if 'level' in new:
            level = new['level']
        else:
            level = None

        if name is None and level is None:
            raise ValueError('The new dictionary must have either key '
                '"name" or "level"')

        olev1 = None
        olev2 = None
        if name is not None:
            qset = OrganizationLevel.objects.filter(name=name)
            if qset:
                olev1 = qset[0]
        if level is not None:
            qset = OrganizationLevel.objects.filter(level=level)
            if qset:
                olev2 = qset[0]

        if olev1 is not None:
            if olev2 is None:
                changed = olev1.update_orglevel_from_dict(new)
                olev = olev1
            else:
                if olev1 == olev2:
                    changed = olev1.update_orglevel_from_dict(new)
                    olev = olev1
                else:
                    raise ValueError('Distinct OrganizationLevels with '
                            'name="{}" ({})  and level="{}" ({}) '
                           'exist'.format( name, olev1, level, olev2))
        elif olev2 is not None:
            changed = olev2.update_orglevel_from_dict(new)
            olev = olev2
        else:
            # No matches, create new
            created = True
            changed = new
            olev = OrganizationLevel.objectcs.create(**new)
        return org, created, changed

    @classmethod
    def root_organization_level(cls):
        """Returns the 'root' OrganizationLevel, ie orglevel w/out parent.

        Returns the root OrganizationLevel if found (first found), or
        None if none found.
        """
        qset = OrganizationLevel.objects.filter(parent__isnull=True)
        if bool(qset):
            return qset[0]
        else:
            return None

    def child_organization_level(self):
        """Returns the OrganizationLevel whose parent is self.

        Returns None if no child found.
        """
        qset = OrganizationLevel.objects.filter(parent=self)
        if qset:
            return qset[0]
        else:
            return None

    @classmethod
    def generate_orglevel_hierarchy_list(cls, validate=False):
        """This generates a hierarchical list of OrganizationLevels.

        This will return a list of OrganizationLevels, with the
        first element of the list being the root OrganizationLevel,
        and each successive element being the (unique) child of
        the previous element, until we reach the final, childless
        element.

        When validate is true, we perform some extra checks to ensure
        a valid org level hierarchy, raising an ValidationError exception 
        if issues are found.  If validate is false (default), we assume a 
        valid hierarchy; the returned value will still a 'hierarchy' even 
        if the hierarchy is not valid, but it might not be unique unless
        the hierarchy is valid.
        """
        retval = []

        # Find root element
        qset = OrganizationLevel.objects.filter(parent__isnull=True)
        if not bool(qset):
            # No root organization level was found 
            # Not an error, return empty list
            return retval
        if validate:
            # In validate mode, make sure the root org level is unique
            if len(qset) > 1:
                tmp = [ x.name for x in qset ]
                tmpstr = ', '.join(tmp)
                raise ValidationError('OrganizationLevel hierarchy '
                    'has multiple parentless members: {}'.format(
                        tmp))
        last_orglevel = qset[0]
        retval.append(last_orglevel)

        # Now repeatedly add child of last_orglevel
        while last_orglevel is not None:
            qset = OrganizationLevel.objects.filter(parent=last_orglevel)
            if not bool(qset):
                last_orglevel=None
            else:
                if validate:
                    # Make sure only a single child
                    if len(qset) > 1:
                        raise ValidationError('OrganizationLevel hierarchy '
                            'issue: orglevel={} has multiple children: '
                            '{}'.format(last_orglevel, ', '.join(list(qset))))
                last_orglevel = qset[0]
                retval.append(last_orglevel)

        return retval

    @classmethod
    def validate_orglevel_hierarchy(cls):
        """Perform various validation checks on OrganizationLevel hierarchy.

        This performs various checks to ensure a valid hierarchy of
        OrganizationLevels, regardless of disable_validation_checks setting.

        An empty hierarchy (i.e. no OrganizationLevels defined) is valid.
        Otherwise, it ensures that:
        1) There is a single 'root' OrganizationLevel (i.e. OrgLevel without
        a parent OrgLevel)
        2) There is a single 'leaf' OrganizationLevel (i.e. OrgLevel without 
        a child OrgLevel.  Note root=leaf is valid)
        3) All other (non-root, non-leaf) OrganizationLevel have exactly one
        parent and one child OrganizationLevel
        4) For every OrganizationLevel, the value for its level data member
        is strictly greater than that of its child (if it has a child), and
        strictly less than that of its parent (if it has a parent).
        5) All name data members are unique.

        If any issues found, raises a ValidationError exception.
        It will also produce a warning if disable_validation_checks is not
        set
        """
        if cls.disable_validation_checks():
            logger.warning('OrganizationLevel disable_validation_checks is '
                'set')
            warnings.warn('OrganizationLevel disable_validation_checks is '
                'set')

        all_org_levels = OrganizationLevel.objects.all()
        if len(all_org_levels) == 0:
            # No OrganizationLevels exist
            # That is a valid hierarchy
            return

        # Use generate_orglevel_hierarchy_list for basic validation
        # This will check that a single root orglevel, and each orglevel
        # in chain has at most a single child orglevel
        org_level_hier = cls.generate_orglevel_hierarchy_list(validate=True)
        if len(all_org_levels) != len(org_level_hier):
            # If valid, org_level_hier must contain all orglevels
            raise ValidationError('OrganizationLevel hierarchy issue: '
                'hierarchy size {} disagrees with total number {} of '
                'OrganizationLevels'.format(len(org_level_hier), 
                    len(all_org_levels)))

        # At this point, all orglevels in org_level_hier, so we have a
        # basic chain and no outliers.
        # Now just ensure levels are OK, names unique, and not too many
        # exporting to Xdmod
        allnames = set()
        lastlevel = None
        xdmod_exporters = set()
        lastorglev = None

        for orglev in org_level_hier:
            level = orglev.level
            if lastlevel is None:
                # We must be on root orglevel, no check needed
                pass
            else:
                # Ensure our level is less than parent
                if not lastlevel > level:
                    raise ValidationError('OrganizationLevel hierarchy issue: '
                            'parent OrgLevel {} with level={} is not greater '
                            'than child OrgLevel {} with level={}'.format(
                                lastorglev, lastlevel, orglev, level))
            lastorglev = orglev
            lastlevel = level

            name = orglev.name
            if name in allnames:
                raise ValidationError('OrganizationLevel hierarchy issue: '
                        'multiple OrganizationLevels with name {}'.format(
                            name))
            allnames.add(name)

            xdmod_exporters.add(orglev)

        # All checks passed
        return

    @classmethod
    def add_organization_level(cls, name, level, parent, export_to_xdmod):
        """Adds a new organization level to the hierarchy.

        This adds a new org level with name, level, export_to_xdmod,  and 
        parent, repairing the hierarchy.  It will also add Organizations if
        needed to repair the Organization hierarchy.

        If the parent is None, then level must be greater than the level
        for any existing org level, and the new level will be the new root
        organization level.  The previous root org level will then but updated 
        to have the new org level as its parent.  If there are Organizations
        having the previous root as their OrgLevel, a new 'Unknown' root-level
        Organization will be created and all the Organizations previously at
        root-level will be made children of it.

        If a parent org level is given, and that parent does not have a
        child org level, than we simply add our new level beneath it.  The
        level given for the new org level must be less than that of the parent.
        For this case, this script is not really needed.

        If a parent org level is given and the parent has a child org level,
        then the given level must be between the parent and child levels,
        and the new org level will be added in between those two in the
        hierarchy.  For each Organization found at the child org level, we will
        create a placeholder Organization at the newly inserted OrgLevel
        and set the new Organization's parent to that of the Organization at
        the child OrgLevel, and sets that Organization's parent to the newly
        inserted Organization.

        For most cases this method will temporarily disable the validation
        checks (which would otherwise prevent the addition of the org level).

        Returns the newly created OrganizationLevel
        """
        if parent is None:
            # No parent organization
            root = cls.root_organization_level()
            if root:
                # A root allocation exists; we will replace as root
                if not level > root.level:
                    raise ValidationError( 'Attempt to install new root '
                        'orglevel {} with level {} is less than existing '
                        'root {} with level {}'.format(
                        name, level, root, root.level))
                # Replace root orglevel
                cls.disable_validation_checks(True)
                newroot = OrganizationLevel(
                        name=name, level=level, parent=None)
                newroot.save()
                root.parent = newroot
                root.save()
                cls.disable_validation_checks(False)

                # Delete any cached toplevel unknown org
                Organization.CACHED_TOPLEVEL_UNKNOWN_ORG = None
                # Are there any Organizations with OrgLevel=root ?
                orgs = Organization.objects.filter(organization_level=root)
                if orgs:
                    # Yes, so we need to create a placeholder root Organization
                    rootorg = Organization.get_or_create_unknown_root()
                    # And make that the parent to all previously root-level
                    # organizations
                    for org in orgs:
                        org.parent=rootorg
                        org.save()
                return newroot
            else:
                # No root allocation (so no hierarchy)
                # Just add the first entry
                newroot = OrganizationLevel(
                        name=name, level=level, parent=None)
                newroot.save()
                return newroot
        else:
            if not parent.level > level:
                raise ValidationError( 'Attempt to install new orglevel '
                    '{} with level {} is more than parent '
                    '{} with level {}'.format(
                    name, level, parent, parent.level))

            # We were given a parent, see if it has a child
            child = OrganizationLevel.objects.filter(parent=parent)
            if child:
                # Child queryset not empty, set child to first
                child = child[0]
                # Parent has a child, we go in between
                if not level > child.level:
                    raise ValidationError( 'Attempt to install new orglevel '
                        '{} with level {} is less than child '
                        '{} with level {}'.format(
                        name, level, child, child.level))
                cls.disable_validation_checks(True)
                newolev = OrganizationLevel(
                        name=name, level=level, parent=None)
                newolev.save()
                child.parent = newolev
                child.save()
                newolev.parent = parent
                newolev.save()
                cls.disable_validation_checks(False)

                # Are there any Organizations with OrgLevel=child ?
                orgs = Organization.objects.filter(organization_level=child)
                for org in orgs:
                    # For each Org at OrgLevel=child, we create a new 
                    # placeholder Org to sit between the child and parent Org
                    uniq_names = Organization.generate_unique_organization_names(
                        code='{}{}'.format('placeholder', org.code),
                        shortname='{}{}'.format('placeholder', org.shortname),
                        longname='{}{}'.format('placeholder', org.longname),
                        parent=org.parent)
                    neworg = Organization(code=uniq_names['code'],
                            shortname=uniq_names['shortname'],
                            longname=uniq_names['longname'],
                            parent=org.parent)
                    neworg.save()
                    org.parent = neworg
                    org.save()
                return newolev
            else:
                # Parent is childless, so simply add
                newolev = OrganizationLevel(
                        name=name, level=level, parent=parent)
                newolev.save()
                return newolev

    def delete_organization_level(self):
        """Delete the invocant organization level from the hierarchy.

        This deletes the invocant org level, repairing the hierarchy.

        There must be no Organizations whose organization_level points
        to the invocant OrganizationLevel which is being deleted.  If
        there are, an exception will be raised.  You must adjust the
        Organization tree appropriately beforehand.  As that likely
        will leave the Organization tree in an invalid state until
        this OrganizationLevel is deleted, you will likely need to
        set Organization.disable_validate_checks to True while making
        those adjustments (and clear after calling this method).

        If the orglevel being deleted has no child orglevel, then everything
        is simple.  If it has a child but no parent (i.e. is the root orglevel),
        we make the child the new root org level before deleting.  If the 
        orglevel being deleted has both a parent and child, we make the
        child's parent the invocant orglevel's parent before deleting the
        invocant.  All but the first case requires temporarily disabling
        the validation checks.
        """
        # See if there are any Organizations with invocant OrgLevel.
        orgs = Organization.objects.filter(organization_level=self)
        if orgs:
            tmp = [ x.fullcode() for x in orgs ]
            raise ValidationError( 'Attempt to delete orglevel '
                '{} without replacement org and with organization '
                '{} referring to it.'.format(
                    self, ', '.join(tmp)))

        # Do we have a parent?
        if self.parent:
            # We have a parent. Do we have a child?
            child = OrganizationLevel.objects.filter(parent=self)
            if child:
                # Have parent and child
                child = child[0]

                # Set the child's parent to parent
                self.disable_validation_checks(True)
                child.parent = self.parent
                self.delete()
                self.disable_validation_checks(False)
                return
            else:
                # Have a parent but no child
                # Just delete it
                self.delete()
                return
        else:
            # No parent, so we are at root level. Do we have a child?
            child = OrganizationLevel.objects.filter(parent=self)
            if child:
                # Have child but no parent
                # Make child new root level
                child = child[0]
                self.disable_validation_checks(True)
                child.parent = None
                child.save()
                self.delete()
                self.disable_validation_checks(False)
                return
            else:
                # No parent or child.  So this is the only OrgLevel
                # Just delete it
                self.delete()
                return

    class Meta:
        ordering = ['-level']

class Organization(TimeStampedModel):
    """This represents an organization, in a multitiered hierarchy.

    All organizational units, regardless of level are stored in this
    table.  Each links back to a specific OrganizationLevel, and can
    (and will unless at the highest organizational level) have a 
    parent which belongs to a higher organizational level.
    """
    
    parent = models.ForeignKey(
            'self', 
            on_delete=models.PROTECT,
            null=True, 
            blank=True)
    organization_level = models.ForeignKey(
            OrganizationLevel, 
            on_delete=models.PROTECT,
            null=False)
    code = models.CharField(
            max_length=512, 
            null=True, 
            blank=False, 
            unique=False,
            help_text='A short code for referencing this organization.  '
                'Typically will be combined with short codes from all parents '
                'to get an unique reference. May not contain hyphen (-)',
            validators=[
                RegexValidator(
                    regex='-',
                    message='Code field may not contain hyphen (-)',
                    inverse_match=True,)
                ])
    shortname = models.CharField(
            max_length=1024, 
            null=True, 
            blank=False, 
            unique=False,
            help_text='A medium length name for this organization, used '
                'in many displays.')
    longname = models.CharField(
            max_length=2048, 
            null=True, 
            blank=False, 
            unique=False,
            help_text='The full name for this organization, for official '
                'contexts')
    is_selectable_for_user = models.BooleanField(
            default=True,
            help_text='This organization can be selected for Users')
    is_selectable_for_project = models.BooleanField(
            default=True,
            help_text='This organization can be selected for Projects')
    # This is a cached top-level/root Unknown org, used for defaulting things
    CACHED_TOPLEVEL_UNKNOWN_ORG = None
    # Disable the validation constraints if true.
    # Intended for temporary use when adding/deleting OrgLevels (see
    # add_organization_level and delete_organization_level methods).
    _disable_validation_checks=False

    def __str__(self):
        return self.shortname

    @classmethod
    def disable_validation_checks(cls, new=None):
        """Accessor/mutator for _disable_validation_checks class data member.

        Because of the 'magic' done by django with class variables of Models,
        we must always use the explicit class name when referring to the
        class variable, otherwise we can end up with instance-like copies.

        To better support this, always use this accessor/mutator for getting or
        setting the value.
        """
        if new is not None:
            Organization._disable_validation_checks = new
        return Organization._disable_validation_checks

    def clean(self):
        """Validation: Ensure parent is of higher level than us.

        If we don't have a parent, then must be at highest organization
        level.
        If we do have a parent, it must be at a higher level and match
        the level of our org level parent.

        This is to prevent infinite recursion.
        """

        # Call base class's clean()
        super().clean()

        if self.disable_validation_checks():
            return

        # Get orglevel and orglevel's parent
        orglevel_obj = self.organization_level
        orglevel = orglevel_obj.level
        orglevel_parent = orglevel_obj.parent

        if orglevel_parent:
            # OrgLevel has a parent, so we are not at the highest level
            # So we must have a parent
            if not self.parent:
                raise ValidationError('Organization {}, level {} '
                        'is not top-level, but does not have parent'.format(
                            self, orglevel))
            # And it must have a higher org level than us
            parent_orglevel = self.parent.organization_level.level
            if parent_orglevel <= orglevel:
                raise ValidationError('Organization {}, level {} '
                        'has parent {} of lower level {}'.format(
                            self, orglevel, self.parent, parent_orglevel))
            # And it must match the level or orglevel_parent
            if parent_orglevel != orglevel_parent.level:
                raise ValidationError('Organization {}, level {} '
                        'has parent {} with level {} != '
                        'level {} of our orglevels parent'.format(
                            self, orglevel, self.parent, 
                            parent_orglevel, orglevel_parent.level))
        else:
            # OrgLevel does not have a parent, so neither should we
            if self.parent:
                raise ValidationError('Organization {}, level {} '
                        'is top-level, but has parent {}'.format(
                            self, orglevel, self.parent))

        return

    def save(self, *args, **kwargs):
        """Override save() to call full_clean first"""
        self.full_clean()
        return super(Organization, self).save(*args, **kwargs)

    @classmethod
    def default_org_pk(cls):
        """Returns the PK of Org user/project objects should default to.

        This just returns the PK of get_or_create_unknown_root, i.e. 
        the top-level/root Unknown object.
        """
        defobj = cls.get_or_create_unknown_root()
        if defobj is None:
            return None
        else:
            return defobj.pk

    def update_organization_from_dict(self, new):
        """Updates Organization to match dictionary.

        The fields of the invocant will be updated to match the
        fields of the dictionary new.  Fields not present in the
        dictionary new are ignored/left unchanged.

        Returns None if no fields have been changed, or a 
        dictionary with keys and values of fields which have been changed.
        """
        retval = {}
        for key, value in new.items():
            if key == 'code':
                if self.code != value:
                    self.code = value
                    retval['code']= value
            elif key == 'shortname':
                if self.shortname != value:
                    self.shortname = value
                    retval['shortname']= value
            elif key == 'longname':
                if self.longname != value:
                    self.longname = value
                    retval['longname']= value
            elif key == 'organization_level':
                if self.organization_level != value:
                    self.organization_level = value.pk
                    retval['organization_level']= value
            elif key == 'parent':
                if self.parent != value:
                    self.parent = value.pk
                    retval['parent']= value
            elif key == 'is_selectable_for_user':
                if self.is_selectable_for_user != value:
                    self.is_selectable_for_user = value
                    retval['is_selectable_for_user']= value
            elif key == 'is_selectable_for_project':
                if self.is_selectable_for_project != value:
                    self.is_selectable_for_project = value
                    retval['is_selectable_for_project']= value
            else:
                raise ValueError('No field {} for {}\n'.format(
                    key, self))

        if retval:
            self.save()
        else:
            retval = None
        return retval

    def ancestors(self):
        """Returns of list ref of all ancestors.

        Returns a list like [grandparent, parent]
        Returns empty list if no parent, otherwise returns the
        parent's ancestors() with parent appended.
        """
        retval = []
        if self.parent:
            retval = self.parent.ancestors()
            retval.append(self.parent)
        return retval
                
    def descendents(self):
        """Returns of list ref of all descendents

        Returns a list like [ child1, child2, ... grandchild1, ... ]
        Returns empty list if no children, otherwise returns a list
        with all of invocant's children, and all of there children, etc.
        """
        # Get immediate children
        import sys
        children = list(Organization.objects.filter(parent=self))
        retval = children
        for child in children:
            # For each child, get it's descendents
            tmp = child.descendents()
            retval.extend(tmp)
        # Deduplicate
        retval = list(set(retval))
        return retval
                
    def fullcode(self):
        """Returns a full code, {parent_code}-{our_code}."""
        retval = self.code
        if self.parent:
            retval = '{pcode}-{code}'.format(
                    pcode=self.parent.fullcode(),
                    code=retval)
        return retval

    def semifullcode(self):
        """Returns full code of our parent, hyphen, our short name."""
        retval = self.shortname
        if self.parent:
            retval = '{pcode}-{code}'.format(
                    pcode=self.parent.fullcode(),
                    code=retval)
        return retval

    def __str__(self):
        return self.fullcode()

    def next_xdmod_exported_organization(self):
        """Returns the next Org whose OrgLevel is exported to xdmod.

        This method returns the next Organization whose OrganizationLevel
        has export_to_xdmod set, starting with the invocant.

        If the OrganizationLevel of the invocant has export_to_xdmod set,
        returns it.  Otherwise, goes through the ancestors of the invocant,
        and returns the first one with export_to_xdmod set.  Returns None
        if no ancestor with export_to_xdmod found.
        """
        orglevel = self.organization_level
        if orglevel.export_to_xdmod:
            return self

        # Invocant is not of an exported OrgLevel
        # We reverse to get parent, grandparent, great-grandparent, ... order
        ancestors = self.ancestors()
        ancestors.reverse()
        for anc in ancestors:
            if anc.organization_level.export_to_xdmod:
                return anc

        # Nothing matched
        return None

    @classmethod
    def create_or_update_organization(self, new):
        """Creates or Updates Organization as needed.

        This method will check if an organization with code and
        parent as given by fields of new.  If no such Organization
        was found, a new Organization is created using the arguments
        from the dictionary new.

        If such an Organization is found, it is updated to match
        the fields listed in new.  Any fields not present as keys to new
        will not be updated.

        Returns a triplet consisting of the Organization found or created,
        a boolean indicating if a new object was created, and a (possibly
        empty) dictionary with the key/values of the fields which have been
        changed.
        """
        created = False
        changed = {}
        if 'code' in new:
            code = new['code']
        else:
            raise ValueError('The new dictionary must have a key "code"')

        if 'parent' in new:
            parent = new['parent']
        else:
            parent = None

        if parent is None:
            qset = Organization.objects.filter(code=code, parent__isnull=True)
        else:
            qset = Organization.objects.filter(code=code, parent=parent)

        if qset:
            # Found a match, so update
            org = qset[0]
            changed = org.update_organization_from_dict(new)
        else:
            # No matches, create a new Org
            org = Organization.objects.create(**new)
            created = True
            changed = new
        return org, created, changed

    @classmethod
    def get_organization_by_fullcode(cls, fullcode):
        """Class method which returns organization with given fullcode.

        This will get the Organization with the given full code. If such
        an Organization object is found, returns it.  Returns None if not
        found.
        """
        codes = fullcode.split('-')
        lastcode = codes[-1]
        orgs = cls.objects.filter(code__exact=lastcode)
        if len(codes) > 1:
            for org in orgs:
                if org.fullcode() == fullcode:
                    return org
            return None
        else:
            if len(list(orgs)) > 0:
                # Should we validate that is unique?  
                # DB constraints say should be
                return list(orgs)[0]
            else:
                return None

    @classmethod
    def get_organization_by_semifullcode(cls, fullcode):
        """Class method which returns organization with given fullcode.

        This will get the Organization with the given full code. If such
        an Organization object is found, returns it.  Returns None if not
        found.
        """
        codes = fullcode.split('-')
        lastcode = codes[-1]
        orgs = cls.objects.filter(shortname__exact=lastcode)
        if len(codes) > 1:
            for org in orgs:
                if org.semifullcode() == fullcode:
                    return org
            return None
        else:
            if len(list(orgs)) > 0:
                # Should we validate that is unique?  
                # DB constraints say should be
                return list(orgs)[0]
            else:
                return None

    @classmethod
    def generate_unique_organization_names(cls, 
            code='Unknown', 
            shortname='Unknown', 
            longname='Unknown', 
            parent=None):
        """This find unique code/shortname/longname for a new Organization.

        Parent can be None for a root level Organization, or reference an
        existing Organization.  We will find a set of code, shortname, and
        longname which begins with the values specified, but does not occur
        among the current children of the parent.  These are returned as
        a dictionary with keys 'code', 'shortname', and 'longname', resp.
        """
        all_children = None
        if parent is None:
            all_children = cls.objects.filter(parent__isnull=True)
        else:
            all_children = cls.objects.filter(parent=parent)

        all_codes = set()
        all_snames = set()
        all_lnames = set()
        for child in all_children:
            all_codes.add(child.code)
            all_snames.add(child.shortname)
            all_lnames.add(child.longname)

        # Find unique values
        retval = {}

        # Get unique code
        if code in all_codes:
            i = 1
            test = '{}{}'.format(code,i)
            while test in all_codes:
                i = i+1
                test = '{}{}'.format(code,i)
            code = test
        retval['code'] = code

        # Get unique shortname
        if shortname in all_snames:
            i = 1
            test = '{}{}'.format(shortname,i)
            while test in all_snames:
                i = i+1
                test = '{}{}'.format(shortname,i)
            shortname = test
        retval['shortname'] = shortname

        # Get unique longname
        if longname in all_lnames:
            i = 1
            test = '{}{}'.format(longname,i)
            while test in all_lnames:
                i = i+1
                test = '{}{}'.format(longname,i)
            longname = test
        retval['longname'] = longname

        return retval

    @classmethod
    def get_or_create_unknown_root(cls, dryrun=False):
        """This returns a 'top-level' Unknown organization.

        It will look for one, first checking if it is cached
        in CACHED_TOPLEVEL_UNKNOWN_ORG, then searching DB, 
        and return if found.  

        If not found, creates one.  The value being returned will
        be cached in UNKNOWN_ORG to speed up future calls.

        If dryrun is set, will not actually create an instance but
        just return None
        """
        if cls.CACHED_TOPLEVEL_UNKNOWN_ORG is not None:
            # We have a cached value, use it
            return cls.CACHED_TOPLEVEL_UNKNOWN_ORG

        # No value cached in UNKNOWN_ORG, look for one in DB
        # To allow this to work when adding a new root orglevel, we
        # need to search for orglevel having no parent, not for org
        # to have no parent (between creation of new root and migrating
        # old root level orgs to new root org, the orgs at old root will
        # have no parent and be picked up)
        qset = cls.objects.filter(
                code='Unknown', 
                #parent__isnull=True,
                organization_level__parent__isnull=True,
                )
        if qset:
            # We got an org with code='Unknown', cache and return first found
            cls.CACHED_TOPLEVEL_UNKNOWN_ORG = qset[0]
            return qset[0]

        if dryrun:
            return None
        #Not found, create one
        orglevel = OrganizationLevel.root_organization_level()
        if not orglevel:
            raise OrganizationLevel.DoesNotExist('No parentless OrganizationLevel found')
        unique_names = cls.generate_unique_organization_names(
                parent=None,
                code='Unknown',
                shortname='Unknown',
                longname='Container for Unknown organizations'
                )

        new = cls.objects.create(
                code=unique_names['code'],
                parent=None,
                organization_level=orglevel,
                shortname=unique_names['shortname'],
                longname=unique_names['longname']
                )
        # Cache it
        cls.CACHED_TOPLEVEL_UNKNOWN_ORG = new
        return new

    @classmethod
    def create_unknown_object_for_dir_string(cls, dirstring, dryrun=False):
        """This creates a placeholder Organization for the 
        given Directory string.

        A new Organization will be created under the top-
        level Unknown Organization, and will create a
        Directory2Organization object refering to it.
        The new Organization will be named Unknown_dddd
        where dddd is some number.

        This is to help facilitate admins fixing things
        afterwards --- either by merging the new directory
        string with an existing Organization or creating 
        a new one.

        The newly created Organization is returned.
        """
        unknown_root = cls.get_or_create_unknown_root(dryrun)
        orglevel = None
        if unknown_root is not None:
            root_orglevel = unknown_root.organization_level
            orglevel = root_orglevel.child_organization_level()
        unique_names = cls.generate_unique_organization_names(
                parent=unknown_root,
                code='Unknown_placeholder',
                shortname='Unknown: {}'.format(dirstring),
                longname='Unknown: {}'.format(dirstring)
                )
        placeholder = cls(
            code=unique_names['code'],
            parent=unknown_root,
            organization_level=orglevel,
            shortname=unique_names['shortname'],
            longname=unique_names['longname']
            )
        if not dryrun:
            placeholder.save()
        tmpid = placeholder.id
        if tmpid is None:
            tmpid = abs(hash(dirstring))
            placeholder.id = tmpid
        placeholder.code = 'Unknown_{}'.format(tmpid)
        if not dryrun:
            placeholder.save()
            Directory2Organization.objects.create(
                    organization=placeholder,
                    directory_string=dirstring).save()
        return placeholder
    
    @classmethod
    def convert_strings_to_orgs(cls, strings, 
            createUndefined=False, dryrun=False):
        """This class method takes a list of strings, and returns 
        a list of organizations.

        Strings should be a list of strings as returned by the 
        directory.  On success it will return a list of unique 
        Organizations corresponding to the strings.

        If a string is given which does not match any strings in 
        Directory2Organization, the behavior will depend on the 
        value of createUndefined.  If createUndefined is False, 
        the string will just be ignored.  If createUndefined is
        True, will call create_unknown_object_for_dir_string and
        include it in the returned list.
        """
        tmporgs = set(())
        for string in strings:
            qset = Directory2Organization.objects.filter(
                directory_string=string)
            if qset:
                # Got an object, add it to tmporgs
                org = qset[0].organization
                tmporgs |= { org }
                continue
            # String did not match a known Directory2Object string
            if not createUndefined:
                # Just ignore it
                continue
            # Create a placeholder organization
            placeholder = \
                    cls.create_unknown_object_for_dir_string(
                    string, dryrun)
            tmporgs |= { placeholder }

        # Convert tmporgs set to list 
        orglist = list(tmporgs)
        return orglist

    @staticmethod
    def add_parents_to_organization_list(organizations):
        """Given a list of organizations, append to the list
        any ancestor organizations to the list.

        Returns the augmented list of Organizations
        """
        tmporgs = set(organizations)
        # Add all ancestors to tmporgs set
        for org in organizations:
            ancestors = org.ancestors()
            tmporgs |= set(ancestors)
        # Now find what was added and append to the list
        toadd = tmporgs - set(organizations)
        return organizations +list(toadd)

    @staticmethod
    def update_user_organizations(user, organizations,
            addParents=False, delete=False, dryrun=False):
        """Updates the organizations associated with user from list
        of Organizations.

        Given an UserProfile and a list of Organizations, update 
        the Organizations associated with the UserProfile.

        Return value is dictionary with keys 'added' and 'removed',
        the values for which are lists of Organization objects
        which were added/removed from the user.

        If addParents is set, will include the ancestors of any
        Organizations in the list as well.
        If delete is set, will disassociated from the UserProfile
        and Organizations not in the (possible augmented with
        parents) Organizations list.
        If dryrun is set, does not actually add/remove Organizations, 
        but still returns as if it did.
        """
        orgs2add = organizations
        if addParents:
            orgs2add = Organization.add_parents_to_organization_list(
                    orgs2add)
        orgs2add = set(orgs2add)

        # Handle special case when (in dryrun) we are given an user
        # who has not been saved to DB yet.  Should only be for dryrun
        oldorgset = set()
        if user.id is not None:
            oldorgset = set(user.organizations.all())
        neworgs = orgs2add - oldorgset
        if not dryrun:
            for org in list(neworgs):
                user.organizations.add(org)

        orgs2del = oldorgset - orgs2add
        orgs2del = list(orgs2del)
        if delete:
            if not dryrun:
                for org in orgs2del:
                    user.organizations.remove(org)
        return {'added': neworgs, 'removed': orgs2del }

    @staticmethod
    def update_project_organizations(project, organizations,
            addParents=False, delete=False, dryrun=False):
        """Updates the organizations associated with project from list
        of Organizations.

        Given an Project and a list of Organizations, update 
        the Organizations associated with the Project.

        Return value is dictionary with keys 'added' and 'removed',
        the values for which are lists of Organization objects
        which were added/removed from the project.

        If addParents is set, will include the ancestors of any
        Organizations in the list as well.
        If delete is set, will disassociated from the UserProfile
        and Organizations not in the (possible augmented with
        parents) Organizations list.
        If dryrun is set, does not actually add/remove Organizations, 
        but still returns as if it did.
        """
        orgs2add = organizations
        if addParents:
            orgs2add = Organization.add_parents_to_organization_list(
                    orgs2add)
        orgs2add = set(orgs2add)
        oldorgset = set(project.organizations.all())
        neworgs = orgs2add - oldorgset
        if not dryrun:
            for org in list(neworgs):
                project.organizations.add(org)

        orgs2del = oldorgset - orgs2add
        orgs2del = list(orgs2del)
        if delete:
            if not dryrun:
                for org in orgs2del:
                    project.organizations.remove(org)
        return { 'added': neworgs, 'removed': orgs2del }

    @staticmethod
    def update_user_organizations_from_dirstrings(
            user, dirstrings, addParents=False, 
            delete=False, createUndefined=False,
            dryrun=False):
        """Updates the organizations associated with user from list
        of directory strings.

        Given an UserProfile and a list of Directory2Organization
        directory_strings, updates the the Organizations 
        associated with the UserProfile.

        Like update_user_organizations, returns a dictionary with 
        keys 'added' and 'removed' with lists of Organization objects
        added/removed.

        Basically, does convert_strings_to_orgs followed by
        update_user_organizations.  addParents, delete, and dryrun passed
        to update_user_organizations, and createUndefined to
        convert_strings_to_orgs.
        """
        orgs2add = Organization.convert_strings_to_orgs(
                strings=dirstrings, 
                createUndefined=createUndefined,
                dryrun=dryrun)
        results = Organization.update_user_organizations(
                user=user, 
                organizations=orgs2add, 
                addParents=addParents, 
                delete=delete,
                dryrun=dryrun)
        return results

    @staticmethod
    def update_project_organizations_from_dirstrings(
            project, dirstrings, addParents=False, 
            delete=False, createUndefined=False, dryrun=False):
        """Updates the organizations associated with project from list
        of directory strings.

        Given an Project and a list of Directory2Organization
        directory_strings, updates the the Organizations 
        associated with the Project.

        Basically, does convert_strings_to_orgs followed by
        update_project_organizations.  addParents, delete, and dryrun passed
        to update_project_organizations, and createUndefined to
        convert_strings_to_orgs.
        """
        orgs2add = Organization.convert_strings_to_orgs(
                dirstrings, createUndefined)
        results = Organization.update_project_organizations(
                project=project, 
                organizations=orgs2add, 
                addParents=addParents, 
                delete=delete,
                dryrun=dryrun,
                )
        return results

    class Meta:
        ordering = ['organization_level', 'code', ]
        constraints = [
                # Require code and parent be pairwise unique
                models.UniqueConstraint(
                    name='organization_code_parent_unique',
                    fields=[ 'code', 'parent' ]
                    ),
                # even when parent=NULL
                models.UniqueConstraint(
                    name='organization_code_nullparent_unique',
                    fields=['code'],
                    condition=Q(parent__isnull=True)
                    ),
                # Similar for shortname
                models.UniqueConstraint(
                    name='organization_shortname_parent_unique',
                    fields=[ 'shortname', 'parent' ]
                    ),
                models.UniqueConstraint(
                    name='organization_shortname_nullparent_unique',
                    fields=['shortname'],
                    condition=Q(parent__isnull=True)
                    ),
                # Similar for longname
                models.UniqueConstraint(
                    name='organization_longname_parent_unique',
                    fields=[ 'longname', 'parent' ]
                    ),
                models.UniqueConstraint(
                    name='organization_longname_nullparent_unique',
                    fields=['longname'],
                    condition=Q(parent__isnull=True)
                    ),
                ]

class Directory2Organization(TimeStampedModel):
    """This table links strings in LDAP or similar directories to organizations.
    """
    organization = models.ForeignKey(
            Organization,
            on_delete=models.CASCADE, 
            null=False,
            blank=False)
    directory_string = models.CharField(
            max_length=1024, 
            null=False,
            blank=False, 
            unique=True)

    def __str__(self):
        return '{}=>{}'.format(self.directory_string,self.organization)


