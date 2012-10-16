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

import placard.models

class BasicLDAPGroupForm(forms.Form):
    cn = forms.CharField(label='CN')

    def clean_cn(self):
        cn = self.cleaned_data['cn']
        groups = placard.models.group.filter(cn=cn)
        if len(groups) > 0:
            raise forms.ValidationError("This group already exists!")
        return cn


class AddGroupForm(forms.Form):
    add_group = forms.ChoiceField(choices=[('','--------------------')]+[(x.gidNumber, x.cn) for x in placard.models.group.objects.all()])

    def save(self, uid):
        conn = LDAPClient()
        group = int(self.cleaned_data['add_group'])
        conn.add_group_member('gidNumber=%s' % group, uid)
        return group


class RenameGroupForm(forms.Form):
    name = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        super(RenameGroupForm, self).__init__(*args, **kwargs)
    
    def clean_name(self):
        name = self.cleaned_data['name']
        return name
        
    def save(self):
        name = self.cleaned_data['name']
        conn = LDAPClient()
        group = self.group
        conn.rename_group('gidNumber=%s' % group.gidNumber, name)
