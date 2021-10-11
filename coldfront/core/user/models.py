from django.contrib.auth.models import User
from django.db import models

from coldfront.core.organization.models import Organization

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_pi = models.BooleanField(default=False)
    organizations = models.ManyToManyField(Organization,
            related_name='users')

    def selectable_organizations(self):
        """Returns the members of organizations which have are selectable.

        I.e. this users organizations which have is_selectable_by_user set.
        For filtering stuff in templates.
        """
        import sys
        sys.stderr.write('[TPTEST] starting selectable_organizations for {}\n'.format(
            self))
        return Organization.objects.filter(users=self,
                is_selectable_for_user=True)


