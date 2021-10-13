import sys

from django.dispatch import receiver
from django_auth_ldap.backend import populate_user
from django.contrib.auth.models import User
from django_auth_ldap.backend import LDAPBackend

from coldfront.core.organization.models import Organization

@receiver(populate_user, sender=LDAPBackend)
def populate_user_organizations(sender, user, ldap_user,  **kwargs):
    sys.stderr.write("[TPTEST] populate_user_organizations called\n")
    sys.stderr.write("[TPTEST] ldap_user={}\n".format(ldap_user))
    sys.stderr.write("[TPTEST] repr(ldap_user)={}\n".format(repr(ldap_user)))
    sys.stderr.write("[TPTEST] dir(ldap_user)={}\n".format(repr(dir(ldap_user))))
    sys.stderr.write("[TPTEST] repr(ldap_user.attrs)={}\n".format(repr(ldap_user.attrs)))
    sys.stderr.write("[TPTEST] dir(ldap_user.attrs)={}\n".format(repr(dir(ldap_user.attrs))))
    # Save user object
    user.save()
    userProfile=user.userprofile
    dirstrings = ldap_user.attrs.get('umDepartment', [])
    sys.stderr.write("[TPTEST] repr(dirstrings) is {}".format(repr(dirstrings)))
    Organization.update_user_organizations_from_dirstrings(
        user=userProfile, dirstrings=dirstrings, addParents=True,
        createUndefined=True)
    


