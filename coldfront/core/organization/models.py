from django.db import models
from model_utils.models import TimeStampedModel
from django.core.exceptions import ValidationError
from django.db.models import Max


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

    name = models.CharField(max_length=512, null=True, blank=False, unique=True)
    level = models.IntegerField(null=False, blank=False, unique=True,
            help_text='The lower this value, the higher this type is in the organization.')
    parent = models.OneToOneField('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

    def clean(self):
        """Validation: ensure our parent has a higher level than us

        If we have a parent, make sure it has a higher level than us.
        If we do not have a parent, make sure there are no other rows
        in table. (UNIQUE on parent does not work, as SQL allows multiple
        rows with NULL for an UNIQUE field).
        """
        # First, call base class's version
        super().clean()
        if self.parent:
            # Has a parent, make sure has higher level than us
            plevel = self.parent.level
            if plevel <= self.level:
                raise ValidationError( 'OrganizationLevel {}, level={} '
                    'has parent {} with lower level {}\n' .format(self, self.level,
                        self.parent, plevel))
        else:
            # No parent, make sure we are the highest level in table
            count = OrganizationLevel.objects.count()
            if count > 0:
                raise ValidationError( 'OrganizationLevel {}, level={} '
                    'has no parent, but {} other rows in table' .format(
                        self, self.level, count))


        return

    def save(self, *args, **kwargs):
        """Override save() to call full_clean first"""
        self.full_clean()
        return super(OrganizationLevel, self).save(*args, **kwargs)
                
    class Meta:
        ordering = ['-level']

class Organization(TimeStampedModel):
    """This represents an organization, in a multitiered hierarchy.

    All organizational units, regardless of level are stored in this
    table.  Each links back to a specific OrganizationLevel, and can
    (and will unless at the highest organizational level) have a 
    parent which belongs to a higher organizational level.
    """
    
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    organization_level = models.ForeignKey(OrganizationLevel, on_delete=models.CASCADE, null=False)
    code = models.CharField(max_length=512, null=True, blank=False, unique=True)
    shortname = models.CharField(max_length=1024, null=True, blank=False, unique=True)
    longname = models.CharField(max_length=2048, null=True, blank=False, unique=True)

    def __str__(self):
        return self.shortname

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

        import sys
        sys.stderr.write('[TPTEST] starting Organization clean()\n')
        # Get orglevel and orglevel's parent
        orglevel_obj = self.organization_level
        sys.stderr.write('[TPTEST] orglevel_obj is {}\n'.format(repr(orglevel_obj)))
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
        return super(OrganizationLevel, self).save(*args, **kwargs)
                
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
        return self.semifullcode()

    class Meta:
        ordering = ['shortname', ]
        constraints = [
                models.UniqueConstraint(
                    name='organization_code_parent_unique',
                    fields=[ 'code', 'parent' ]
                    )
                ]


