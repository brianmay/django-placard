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
from andsome.middleware.threadlocals import get_current_user

import datetime, time

from andsome.util import is_password_strong

import placard.models

class BasicLDAPUserForm(forms.Form):
    """ Basic form used for sub classing """
    givenName = forms.CharField(label='First Name')
    sn = forms.CharField(label='Last Name')
    


class LDAPAdminPasswordForm(forms.Form):
    """ Password change form for admin. No old password needed. """
    new1 = forms.CharField(widget=forms.PasswordInput(), label=u'New Password')
    new2 = forms.CharField(widget=forms.PasswordInput(), label=u'New Password (again)')

    def clean(self):
        data = self.cleaned_data

        if data.get('new1') and data.get('new2'):

            if data['new1'] != data['new2']:
                raise forms.ValidationError(u'You must type the same password each time')

            if not is_password_strong(data['new1']):
                raise forms.ValidationError(u'Your password was found to be insecure, a good password has a combination of letters (upercase, lowercase), numbers and is at least 8 characters long.')
            
            return data

        
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
