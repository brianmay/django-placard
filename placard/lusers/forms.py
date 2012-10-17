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


""" placard.lusers.forms """

from django import forms
import django.conf

import datetime, time

from andsome.middleware.threadlocals import get_current_user
from andsome.util import is_password_strong

import placard.models

class BasicLDAPUserForm(forms.Form):
    """ Basic form used for sub classing """
    uid = forms.CharField(label='Username')
    givenName = forms.CharField(label='First Name')
    sn = forms.CharField(label='Last Name')
    homeDirectory = forms.CharField(label='Home Directory')
    primary_group = forms.CharField(label='Primary Group')

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super(BasicLDAPUserForm, self).__init__(*args, **kwargs)

        if self.account is None:
            return

        self.fields['uid'].widget.attrs['readonly'] = True

        for name in [ 'uid', 'givenName', 'sn', 'homeDirectory' ]:
            value = getattr(self.account, name)
            self.initial[name] = value

        primary_group = self.account.primary_group
        if primary_group is not None:
            self.initial['primary_group'] = primary_group.cn

    def clean_uid(self):
            value = self.cleaned_data['uid']
            if self.account is not None:
                if self.account.uid != value:
                    raise forms.ValidationError(u'Cannot change value of uid')
            return value

    def clean_primary_group(self):
        try:
            group = placard.models.group.objects.get(cn=self.cleaned_data['primary_group'])
        except placard.models.group.DoesNotExist:
            raise forms.ValidationError(u'Cannot find primary group')
        return group

    def save(self):
        if self.account is None:
            account = placard.models.account()
        else:
            account = self.account
        for name in [ 'givenName', 'sn', 'homeDirectory', 'primary_group' ]:
            value = self.cleaned_data[name]
            setattr(account, name, value)
        account.save()


class LDAPAdminPasswordForm(forms.Form):
    """ Password change form for admin. No old password needed. """
    new1 = forms.CharField(widget=forms.PasswordInput(), label=u'New Password')
    new2 = forms.CharField(widget=forms.PasswordInput(), label=u'New Password (again)')

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super(LDAPAdminPasswordForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = self.cleaned_data

        if data.get('new1') and data.get('new2'):

            if data['new1'] != data['new2']:
                raise forms.ValidationError(u'You must type the same password each time')

            if not is_password_strong(data['new1']):
                raise forms.ValidationError(u'Your password was found to be insecure, a good password has a combination of letters (upercase, lowercase), numbers and is at least 8 characters long.')

            return data

    def save(self):
        data = form.cleaned_data
        self.account.change_password(data['new1'], django.conf.settings.LDAP_PASSWD_SCHEME)
        self.account.save()

class LDAPPasswordForm(LDAPAdminPasswordForm):
    """ Password change form for user. Muse specify old password. """
    old = forms.CharField(widget=forms.PasswordInput(), label='Old password')

    def clean_old(self):
        user = get_current_user()
        luser = placard.models.account.objects.get(uid=user.username)
        if not luser.check_password(self.cleaned_data['old']):
            raise forms.ValidationError(u'Your old password was incorrect')
        return self.cleaned_data['old']


class AddMemberForm(forms.Form):
    """ Add a user to a group form """
    add_user = forms.ChoiceField(choices=[('','-------------')]+[(x.uid, x.cn) for x in placard.models.account.objects.all()])

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        super(AddMemberForm, self).__init__(*args, **kwargs)

    def save(self):
        try:
            user = placard.models.account.objects.get(uid=self.cleaned_data['add_user'])
        except placard.models.account.DoesNotExist:
            raise django.http.Http404()
        self.group.secondary_accounts.add(user)

