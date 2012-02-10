# Copyright 2010 VPAC
#
# This file is part of django-placard.
#
# django-placard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# django-placard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with django-placard  If not, see <http://www.gnu.org/licenses/>.


from django.test.client import Client
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

import unittest

from placard.server import slapd
from placard.client import LDAPClient
from placard.misc.test_data import test_ldif
from placard.tldap import transaction
from placard import exceptions
import ldap

server = None

class UserAPITest(unittest.TestCase):
    def setUp(self):
        global server
        server = slapd.Slapd()
        server.set_port(38911)
        server.start()
        base = server.get_dn_suffix()
        
        server.ldapadd("\n".join(test_ldif)+"\n")

        self.client = Client()
        self.server = server
            
    def tearDown(self):
        self.server.stop()


    @transaction.commit_on_success()
    def test_get_users(self):
        c = LDAPClient()
        self.failUnlessEqual(len(c.get_users()), 3)
        
    @transaction.commit_on_success()
    def test_get_user(self):
        c = LDAPClient()      
        u = c.get_user('uid=testuser3')
        self.failUnlessEqual(u.mail, 't.user3@example.com')
                             
    @transaction.commit_manually()
    def test_delete_user(self):
        c = LDAPClient()
        self.failUnlessEqual(len(c.get_users()), 3)
        c.delete_user('uid=testuser2')
        c.commit()
        self.failUnlessEqual(len(c.get_users()), 2)
                
    @transaction.commit_on_success()
    def test_in_ldap(self):
        c = LDAPClient()
        self.assertTrue(c.in_ldap('uid=testuser1'))
        self.assertFalse(c.in_ldap('uid=testuser4'))
        
    @transaction.commit_on_success()
    def test_update_user(self):
        c = LDAPClient()
        u = c.get_user('uid=testuser1')
        self.failUnlessEqual(u.sn, 'User')  
        c.update_user('uid=%s' % u.uid, sn='Bloggs')
        c.commit()
        u = c.get_user('uid=testuser1')
        self.failUnlessEqual(u.sn, 'Bloggs')

    @transaction.commit_on_success()
    def test_update_user_no_modifications(self):
        c = LDAPClient()
        u = c.get_user('uid=testuser1')
        self.failUnlessEqual(u.sn, 'User')  
        c.update_user('uid=%s' % u.uid, sn='User')
        u = c.get_user('uid=testuser1')
        self.failUnlessEqual(u.sn, 'User')

    @transaction.commit_manually()
    def test_lock_unlock(self):
        c = LDAPClient()
        self.failUnlessEqual(c.is_locked('uid=testuser1'), False)
        c.lock_user('uid=testuser1')
        c.commit()
        self.failUnlessEqual(c.is_locked('uid=testuser1'), True)
        c.unlock_user('uid=testuser1')
        c.commit()
        self.failUnlessEqual(c.is_locked('uid=testuser1'), False)

    @transaction.commit_on_success()
    def test_user_search(self):
        c = LDAPClient()
        users = c.search_users(['User',])
        self.failUnlessEqual(len(users), 3)

    @transaction.commit_on_success()
    def test_user_search_one(self):
        c = LDAPClient()
        users = c.search_users(['testuser1',])
        self.failUnlessEqual(len(users), 1)

    @transaction.commit_on_success()
    def test_user_search_empty(self):
        c = LDAPClient()
        users = c.search_users(['nothing',])
        self.failUnlessEqual(len(users), 0)

    @transaction.commit_on_success()
    def test_user_search_multi(self):
        c = LDAPClient()
        users = c.search_users(['test', 'user'])
        self.failUnlessEqual(len(users), 3)

    def test_transactions(self):
        c = LDAPClient()
        rdn = getattr(settings, 'LDAP_USER_RDN', 'uid')

        # test explicit roll back
        with transaction.commit_on_success():
            c.add_user(uid="tux", givenName="Tux",sn="Torvalds",telephoneNumber="000",mail="tuz@example.org",o="Linux Rules",userPassword="silly", schacCountryOfResidence="AU",auEduPersonSharedToken="shared")
#            c.update_user("uid=tux", sn="Gates")
            c.rollback()
        self.assertRaises(exceptions.DoesNotExistException, c.get_user, "uid=tux")

        # test roll back on exception
        try:
            with transaction.commit_on_success():
                c.add_user(uid="tux", givenName="Tux",sn="Torvalds",telephoneNumber="000",mail="tuz@example.org",o="Linux Rules",userPassword="silly", schacCountryOfResidence="AU",auEduPersonSharedToken="shared")
#                c.update_user("uid=tux", sn="Gates")
                raise RuntimeError("testing failure")
        except RuntimeError:
            pass
        self.assertRaises(exceptions.DoesNotExistException, c.get_user, "uid=tux")

        # test success commits
        with transaction.commit_on_success():
            c.add_user(uid="tux", givenName="Tux",sn="Torvalds",telephoneNumber="000",mail="tuz@example.org",o="Linux Rules",userPassword="silly", schacCountryOfResidence="AU",auEduPersonSharedToken="shared")
#            c.update_user("uid=tux", sn="Gates")
        self.assertEqual(c.get_user("uid=tux").sn, "Torvalds")

        c.update_user("uid=tux", sn="Gates")

        # test success when 3rd statement fails; need to roll back 2nd and 1st statements
        with transaction.commit_on_success():
            c.update_user("uid=tux", sn="Milkshakes")
            self.assertEqual(c.get_user("uid=tux").sn, "Milkshakes")
            c.update_user("uid=tux", sn="Bannas")
            self.assertEqual(c.get_user("uid=tux").sn, "Bannas")
            # next statement will fail when executed because tux already exists
            c.add_user(uid="tux", givenName="Tux",sn="Torvalds",telephoneNumber="000",mail="tuz@example.org",o="Linux Rules",userPassword="silly", schacCountryOfResidence="AU",auEduPersonSharedToken="shared")
            self.assertRaises(ldap.ALREADY_EXISTS, c.commit)
        self.assertEqual(c.get_user("uid=tux").sn, "Gates")

        # test roll back on error of delete and add of same user
        with transaction.commit_on_success():
            c.delete_user("uid=tux")
            self.assertRaises(exceptions.DoesNotExistException, c.get_user, "uid=tux")
            c.add_user(uid="tux", givenName="Tux",sn="Torvalds",telephoneNumber="000",mail="tuz@example.org",o="Linux Rules",userPassword="silly", schacCountryOfResidence="AU",auEduPersonSharedToken="shared")
            c.add_user(uid="testuser1", givenName="Tux",sn="Torvalds",telephoneNumber="000",mail="tuz@example.org",o="Linux Rules",userPassword="silly", schacCountryOfResidence="AU",auEduPersonSharedToken="shared")
            self.assertRaises(ldap.ALREADY_EXISTS, c.commit)
        self.assertEqual(c.get_user("uid=tux").sn, "Gates")

        # test delate and add same user
        with transaction.commit_on_success():
            c.delete_user("uid=tux")
            self.assertRaises(exceptions.DoesNotExistException, c.get_user, "uid=tux")
            c.add_user(uid="tux", givenName="Tux",sn="Torvalds",telephoneNumber="000",mail="tuz@example.org",o="Linux Rules",userPassword="silly", schacCountryOfResidence="AU",auEduPersonSharedToken="shared")
        self.assertEqual(c.get_user("uid=tux").sn, "Torvalds")

        # test delate
        with transaction.commit_on_success():
            c.delete_user("uid=tux")
        self.assertRaises(exceptions.DoesNotExistException, c.get_user, "uid=tux")
        
        
class UserViewsTests(TestCase):

    def setUp(self):
        global server
        server = slapd.Slapd()
        server.set_port(38911)
        server.start()
        base = server.get_dn_suffix()
        
        server.ldapadd("\n".join(test_ldif)+"\n")

        self.server = server

        try:
            super_user = User.objects.create_user('super', 'sam@vpac.org', 'aq12ws')
            super_user.is_superuser = True
            super_user.save()
        except:
            pass

            
    def tearDown(self):
        self.server.stop()

    def test_user_list(self):
        response = self.client.get(reverse('plac_user_list'))
        self.failUnlessEqual(response.status_code, 200)

    def test_user_detail(self):
        response = self.client.get(reverse('plac_user_detail', args=['testuser1']))
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get(reverse('plac_user_detail', args=['nousers']))
        self.failUnlessEqual(response.status_code, 404)

    def test_delete_view(self):
        response = self.client.get(reverse('plac_user_delete', args=['testuser1']))
        self.failUnlessEqual(response.status_code, 302)
        self.client.login(username='super', password='aq12ws')
        response = self.client.get(reverse('plac_user_delete', args=['testuser1']))
        self.failUnlessEqual(response.status_code, 200)

    def test_user_verbose(self):
        response = self.client.get(reverse('plac_user_detail_verbose', args=['testuser2']))
        self.failUnlessEqual(response.status_code, 302)
        self.client.login(username='super', password='aq12ws')
        response = self.client.get(reverse('plac_user_detail_verbose', args=['testuser2']))
        self.failUnlessEqual(response.status_code, 200)

    def test_lock_user_view(self):
        response = self.client.get(reverse('plac_user_detail_verbose', args=['testuser2']))
        
    def test_lock_unlock_user_view(self):
        c = LDAPClient()
        self.failUnlessEqual(c.is_locked('uid=testuser2'), False)

        self.client.login(username='super', password='aq12ws')        
        response = self.client.get(reverse('plac_lock_user', args=['testuser2']))
        self.failUnlessEqual(c.is_locked('uid=testuser2'), True)

        response = self.client.get(reverse('plac_unlock_user', args=['testuser2']))
        self.failUnlessEqual(c.is_locked('uid=testuser2'), False)


class PasswordTests(TestCase):

    def setUp(self):
        global server
        server = slapd.Slapd()
        server.set_port(38911)
        server.start()
        base = server.get_dn_suffix()
        
        server.ldapadd("\n".join(test_ldif)+"\n")

        self.server = server

        try:
            super_user = User.objects.create_user('super', 'sam@vpac.org', 'aq12ws')
            super_user.is_superuser = True
            super_user.save()
        except:
            pass

            
    def tearDown(self):
        self.server.stop()


    def test_api(self):
        c = LDAPClient()      
        c.change_password('uid=testuser3', raw_password='aq12ws')
        self.assertTrue(c.check_password('uid=testuser3', 'aq12ws'), True)
        c.change_password('uid=testuser3', raw_password='qwerty')
        self.assertTrue(c.check_password('uid=testuser3', 'qwerty'), True)

    def test_admin_view(self):
        c = LDAPClient()      
        response = self.client.get(reverse('plac_change_password', args=['testuser1']))
        self.failUnlessEqual(response.status_code, 302)
        self.client.login(username='super', password='aq12ws')
        response = self.client.get(reverse('plac_change_password', args=['testuser1']))
        self.failUnlessEqual(response.status_code, 200)
        
        response = self.client.post(reverse('plac_change_password', args=['testuser1']), {'new1': 'aq12ws222', 'new2': 'aq12ws222'})
        self.failUnlessEqual(response.status_code, 302)
        self.assertTrue(c.check_password('uid=testuser1', 'aq12ws222'), True)

    def test_user_view(self):
        c = LDAPClient()
        c.change_password('uid=testuser2', raw_password='aq12ws')
        luser = c.get_user('uid=testuser2')
        user = User.objects.create_user(luser.uid, luser.mail, 'aq12ws')

        response = self.client.get(reverse('plac_user_password'))
        self.failUnlessEqual(response.status_code, 302)

        self.client.login(username='testuser2', password='aq12ws')

        response = self.client.get(reverse('plac_change_password', args=['testuser1']))
        self.failUnlessEqual(response.status_code, 403)

        response = self.client.get(reverse('plac_user_password'))
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.post(reverse('plac_user_password'), {'old': 'aq12ws', 'new1': 'aq12ws222', 'new2': 'aq12ws222'})
        self.failUnlessEqual(response.status_code, 302)
        self.assertTrue(c.check_password('uid=testuser2', 'aq12ws222'), True)

        
