from django.dispatch import receiver
from django_auth_ldap.backend import populate_user
from django.contrib.auth.models import User
from django_auth_ldap.backend import LDAPBackend

from coldfront.core.organization.models import Organization

@receiver(populate_user, sender=LDAPBackend)
def populate_user_organizations(sender, user, ldap_user,  **kwargs):
    # Save user object
    user.save()
    userProfile=user.userprofile
    dirstrings = ldap_user.attrs.get('umDepartment', [])
    Organization.update_user_organizations_from_dirstrings(
        user=userProfile, dirstrings=dirstrings, addParents=True,
        createUndefined=True)
    


