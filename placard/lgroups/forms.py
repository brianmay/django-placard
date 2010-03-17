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


from django import forms

from placard.client import LDAPClient

class BasicLDAPGroupForm(forms.Form):
    cn = forms.CharField(label='CN')

    def save(self):
        data = self.cleaned_data
        conn = LDAPClient()
        conn.add_group(**data)


class AddGroupForm(forms.Form):
    add_group = forms.ChoiceField(choices=[('','--------------------')]+[(x.gidNumber, x.name()) for x in LDAPClient().get_groups()])

    def save(self, uid):
        conn = LDAPClient()
        conn.add_group_member('gidNumber=%s' % self.cleaned_data['add_group'], uid)
