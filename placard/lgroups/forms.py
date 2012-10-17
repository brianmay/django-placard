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

import django.http

class BasicLDAPGroupForm(forms.Form):
    cn = forms.CharField(label='CN')

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        super(BasicLDAPGroupForm, self).__init__(*args, **kwargs)

    def clean_cn(self):
        cn = self.cleaned_data['cn']
        groups = placard.models.group.objects.filter(cn=cn)
        if len(groups) > 0:
            raise forms.ValidationError("This group already exists!")
        return cn

    def save(self):
        if self.group is None:
            group = placard.models.group()
        else:
            group = self.group
        group.cn = self.cleaned_data['cn']
        group.save()


class AddGroupForm(forms.Form):
    add_group = forms.ChoiceField(choices=[('','--------------------')]+[(x.gidNumber, x.cn) for x in placard.models.group.objects.all()])

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super(AddGroupForm, self).__init__(*args, **kwargs)

    def save(self):
        try:
            group = placard.models.group.objects.get(gidNumber=self.cleaned_data['add_group'])
        except placard.models.group.DoesNotExist:
            raise django.http.Http404()
        self.account.secondary_groups.add(group)


class RenameGroupForm(forms.Form):
    name = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        super(RenameGroupForm, self).__init__(*args, **kwargs)
        self.initial = { 'name': self.group.cn }

    def clean_name(self):
        name = self.cleaned_data['name']
        return name

    def save(self):
        name = self.cleaned_data['name']
        self.group.rename(cn=name)
