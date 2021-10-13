import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

from coldfront.core.utils.common import import_from_settings
from coldfront.core.organization.models import Organization
from coldfront.core.user.models import UserProfile
from coldfront.plugins.ldap_user_search.utils import LDAPUserSearch

ORGANIZATION_LDAP_USER_ATTRIBUTE = import_from_settings(
        'ORGANIZATION_LDAP_USER_ATTRIBUTE', None)


class Command(BaseCommand):
    help = 'Updates Organizations for user from LDAP'

    def add_arguments(self, parser):
        def_delimiter = '|'

        parser.add_argument('-u', '--username', '--user',
                help='Username of user to add.  Required.',
                required=True,
                dest='username',
                )
        parser.add_argument('--lastname', '--last', 
                help='Last name for user.  Required unless can pickup from LDAP',
                dest='lastname',
                )
        parser.add_argument('--firstname', '--first', 
                help='First name for user.  Required unless can pickup from LDAP',
                dest='firstname',
                )
        parser.add_argument('--email', '--mail', 
                help='Email address for user.  Defaults from LDAP if possible, '
                    'otherwise from username.',
                dest='email',
                )
        parser.add_argument('--inactive',
                action='store_true',
                help='If set, we will add user as inactive.',
                dest='inactive',
                    )
        parser.add_argument('--staff',
                action='store_true',
                help='Adds user as staff user',
                dest='staff',
                    )
        parser.add_argument('--superuser',
                action='store_true',
                help='Adds user as superuser',
                dest='superuser',
                    )
        parser.add_argument('--organization', '--fullcode', '--org',
                action='append',
                help='This gives the fullcode of Organization to add new '
                    'user to.  Maybe repeated for multiple organizations.',
                default=[],
                dest='organizations',
                    )
        parser.add_argument('--dryrun',
                action='store_true',
                help='If set, we will do the LDAP search but print results '
                    'rather than applying them.  Implies verbosity >= 1.',
                dest='dryrun',
                    )
        parser.add_argument('--update',
                action='store_true',
                help='Update existing user.',
                dest='update',
                    )
        parser.add_argument('--noldap',
                action='store_true',
                help='If set, do not lookup attributes for user in LDAP.',
                dest='noldap',
                    )
        parser.add_argument('--parent-orgs', '--parent_orgs', '--parents',
                action='store_true',
                help='If set, add parent Organizations of any orgs being '
                    'added to the user.',
                dest='addparents',
                    )
        parser.add_argument('--create-placeholder-orgs', '--create',
                '--placeholder', '--create_placeholder_orgs',
                action='store_true',
                help='If set, create placeholder Organizations for '
                    'directory_strings not found in Directory2Organization.',
                dest='placeholder',
                    )
        parser.add_argument('--delete-orgs', '--delete_orgs', '--delete',
                action='store_true',
                help='If set, when updating existing user, will delete '
                    'any Organizations not listed.',
                dest='delete',
                    )
        return

    def update_user_profile(self, user_profile, options):
        """Updates existing user profile according to options provided.
        """
        username = user_profile.user.username
        if username != options['username']:
            raise CommandError('Username mismatch in update_user_profile: '
                    'options has {}, profile has {}'.format(
                        options['username'], username))

        lastname = options['lastname']
        firstname = options['firstname']
        email = options['email']
        inactive = options['inactive']
        staff = options['staff']
        superuser = options['superuser']
        update = options['update']
        dryrun = options['dryrun']
        verbosity = options['verbosity']
        fullcodes = options['organizations']
        noldap = options['noldap']
        create_placeholder = options['placeholder']
        parent_orgs = options['addparents']
        delete_orgs = options['delete']

        v_or_d_text = '[VERBOSE]'
        if dryrun:
            v_or_d_text = '[DRYRUN]'
            if not verbosity:
                verbosity=1

        def verbose(string):
            if verbosity:
                sys.stderr.write('{} {}\n'.format(
                    v_or_d_text, string))
            return

        # Convert fullcodes to organizations
        orgs = []
        for fullcode in fullcodes:
            org = Organization.get_organization_by_fullcode(fullcode)
            if org is None:
                raise CommandError('No organization with fullcode={} '
                        'found.'.format(fullcode))
            orgs.append(org)

        if not noldap:
            ldap = LDAPUserSearch(
                    user_search_string=username,
                    search_by='username_only')
            results = ldap.search_a_user(
                    user_search_string=username,
                    search_by='username_only')
            if results:
                userrec = results[0]
                if 'last_name' in userrec:
                    if not lastname:
                        lastname = userrec['last_name']
                if 'first_name' in userrec:
                    if not firstname:
                        firstname = userrec['first_name']
                if 'email' in userrec:
                    if not email:
                        email = userrec['email']
                if 'directory_strings' in userrec:
                    dstrings = userrec['directory_strings']
                    orgs2add = Organization.convert_strings_to_orgs(
                            strings=dstrings, 
                            createUndefined=create_placeholder,
                            dryrun=dryrun)
                    orgs.extend(orgs2add)

        if not lastname:
            raise CommandError('No lastname given for {} and unable to '
                'default'.format(username))
        if not firstname:
            raise CommandError('No firstname given for {} and unable to '
                'default'.format(username))
        if not email:
            email='{}@umd.edu'.format(username)

        user = user_profile.user
        changed = False
        if lastname != user.last_name:
            if dryrun or verbosity:
                verbose('Change lastname for {} from "{}" to "{}"'.format(
                    username, user.last_name, lastname))
            user.last_name = lastname
            changed = True
        if firstname != user.first_name:
            if dryrun:
                verbose('Change firstname for {} from "{}" to "{}"'.format(
                    username, user.first_name, firstname))
            user.first_name = firstname
            changed = True
        if email != user.email:
            if dryrun:
                verbose('Change email for {} from "{}" to "{}"'.format(
                    username, user.email, email))
            user.email = email
            changed = True
        if (not inactive) != user.is_active:
            if dryrun:
                verbose('Change is_active for {} from "{}" to "{}"'.format(
                    username, user.is_active, (not inactive) ))
            user.is_active = not inactive
            changed = True
        if staff != user.is_staff:
            if dryrun:
                verbose('Change is_staff for {} from "{}" to "{}"'.format(
                    username, user.is_staff, staff))
            user.is_staff = staff
            changed = True
        if superuser != user.is_superuser:
            if dryrun:
                verbose('Change is_superuser for {} from "{}" to "{}"'.format(
                    username, user.is_superuser, superuser))
            user.is_superuser = superuser
            changed = True
        if changed:
            if not dryrun:
                user.save()
        results = Organization.update_user_organizations(
                user=user_profile,
                organizations=orgs,
                addParents=parent_orgs,
                delete=delete_orgs,
                dryrun=dryrun,
                )
        if dryrun or verbosity:
            tmporgs = results['added']
            for org in tmporgs:
                verbose('Add organization {} to user {}'.format(
                    org.fullcode(), username))
            tmporgs = results['removed']
            for org in tmporgs:
                verbose('Removed organization {} from user {}'.format(
                    org.fullcode(), username))
        return


    def handle(self, *args, **options):

        username = options['username']

        update = options['update']
        dryrun = options['dryrun']
        verbosity = options['verbosity']

            
        v_or_d_text = '[VERBOSE]'
        if dryrun:
            v_or_d_text = '[DRYRUN]'
            if not verbosity:
                verbosity=1

        def verbose(string):
            if verbosity:
                sys.stderr.write('{} {}\n'.format(
                    v_or_d_text, string))
            return

        # Check for existing user
        qset = UserProfile.objects.filter(user__username=username)
        if qset:
            if len(qset) > 1:
                raise CommandError('Multiple profiles matching username={} '
                        'found.  Aborting.'.format(username))
            if update:
                verbose('Updating existing user {}'.format(username))
                uprof = qset[0]
                self.update_user_profile(uprof, options)
            else:
                raise CommandError('Attempting to create existing user '
                    'username={}, aborting.'.format(username))
        else:
            verbose('Creating new user {}'.format(username))
            user = User(username=username)
            if dryrun:
                uprof = UserProfile(user=user)
            else:
                user.save()
                uprof = user.userprofile
            if not dryrun:
                uprof.save()
            self.update_user_profile(uprof, options)
        return
