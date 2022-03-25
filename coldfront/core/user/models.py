from django.contrib.auth.models import User
from django.db import models

from coldfront.core.organization.models import Organization

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_pi = models.BooleanField(default=False)
    primary_organization = models.ForeignKey(Organization,
            null=True,
            on_delete=models.PROTECT,
            )
    additional_organizations = models.ManyToManyField(Organization,
            related_name='additional_users', blank=True)

    def __str__(self):
        return 'Profile for {}'.format(self.user.username)

    def all_organizations(self):
        """Returns a list of all organizations for this user.

        The primary_organization, if any, is first, followed by
        any additonal_organizations.  If the primary org is also in
        additional_orgs it will not be repeated.
        """
        allorgs = []
        if self.primary_organization:
                allorgs.append(self.primary_organization)
        for org in self.additional_organizations.all():
            if self.primary_organization:
                if org != self.primary_organization:
                    allorgs.append(org)
            else:
                allorgs.append(org)
        return allorgs
