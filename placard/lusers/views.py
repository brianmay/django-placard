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


from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings
from django.http import HttpResponseRedirect, Http404, HttpResponseForbidden
from django.contrib.auth.decorators import permission_required, login_required
from django.core.urlresolvers import reverse
from django.contrib import messages

from andsome.util.filterspecs import Filter, FilterBar

from placard.lgroups.forms import AddGroupForm
from placard.lusers.forms import BasicLDAPUserForm, LDAPAdminPasswordForm, LDAPPasswordForm

import tldap
import placard.models

def user_list(request):
    if request.REQUEST.has_key('group'):
        try:
            group = placard.models.group.objects.get(gidNumber=request.GET['group'])
        except placard.models.group.DoesNotExist:
            raise Http404
        user_list = group.secondary_account.all()
    else:
        user_list = placard.models.account.objects.all()

    if request.REQUEST.has_key('q'):
        term_list = request.REQUEST['q'].lower().split(' ')
        for term in term_list:
            user_list = user_list.filter(tldap.Q(uid__contains=term) | tldap.Q(cn__contains=term))

    filter_list = []
    group_list = {}
    for group in placard.models.group.objects.all():
        group_list[group.gidNumber] = group.cn

    filter_list.append(Filter(request, 'group', group_list))
    filter_bar = FilterBar(request, filter_list)

    return render_to_response('lusers/user_list.html', locals(), context_instance=RequestContext(request))


def user_detail(request, username):
    try:
        luser = placard.models.account.objects.get(uid=username)
    except placard.models.account.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = AddGroupForm(request.POST, account=luser)
        if form.is_valid():
            form.save()
            messages.info(request, u'User %s has been added to group %s.' % (luser, group)) 
            return HttpResponseRedirect(reverse("plac_user_detail",kwargs={ 'username': luser.uid }))
    else:
        form = AddGroupForm(account=luser)

    return render_to_response('lusers/user_detail.html', locals(), context_instance=RequestContext(request))


def add_edit_user(request, username=None, form=BasicLDAPUserForm, template_name='lusers/user_form.html'):
    UserForm = form

    if (request.user.username != username) and (not request.user.has_perm('auth.add_user')):
        return HttpResponseForbidden()

    if username is not None:
        try:
            ldap_user = placard.models.account.objects.get(uid=username)
        except placard.models.account.DoesNotExist:
            raise Http404
    else:
        ldap_user = None

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, account=ldap_user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("plac_user_detail",kwargs={ 'username': ldap_user.uid }))
    else:
        form = UserForm(account=ldap_user)
    
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))
 

@login_required
def user_edit(request, form, template_name):

    return add_edit_user(request, request.user.username, form, template_name)
    

@login_required
def change_password(request, username, password_form=LDAPAdminPasswordForm, template='lusers/password_form.html', redirect_url=None):

    if (request.user.username != username) and (not request.user.has_perm('auth.change_user')):
        return HttpResponseForbidden()

    PasswordForm = password_form

    try:
        ldap_user = placard.models.account.objects.get(uid=username)
    except placard.models.account.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        
        form = PasswordForm(request.POST, account=ldap_user)
        if form.is_valid():
            data = form.cleaned_data
            ldap_user.change_password(data['new1'], settings.LDAP_PASSWD_SCHEME)
            ldap_user.save()

            messages.info(request,'Password changed successfully')
            if redirect_url:
                return HttpResponseRedirect(redirect_url)
            return HttpResponseRedirect(reverse('plac_user_detail', args=[username]))              
    else:
        form = PasswordForm(account=ldap_user)

    return render_to_response(template, locals(), context_instance=RequestContext(request))

@login_required
def user_password_change(request, redirect_url=None):

    return change_password(request, request.user.username, LDAPPasswordForm, 'lusers/user_password_form.html', redirect_url)

@permission_required('auth.delete_user')
def delete_user(request, username):

    if request.method == 'POST':
        try:
            ldap_user = placard.models.account.objects.get(uid=username)
        except placard.models.account.DoesNotExist:
            raise Http404
        ldap_user.delete()
        return HttpResponseRedirect(reverse('plac_user_list'))
    
    return render_to_response('lusers/user_confirm_delete.html', locals(), context_instance=RequestContext(request))


@permission_required('auth.change_user')
def lock_user(request, username):
    try:
        ldap_user = placard.models.account.objects.get(uid=username)
    except placard.models.account.DoesNotExist:
        raise Http404

    ldap_user.lock()

    return HttpResponseRedirect(luser.get_absolute_url())

@permission_required('auth.change_user')
def unlock_user(request, username):
    try:
        ldap_user = placard.models.account.objects.get(uid=username)
    except placard.models.account.DoesNotExist:
        raise Http404

    ldap_user.unlock()

    return HttpResponseRedirect(luser.get_absolute_url())

@permission_required('auth.change_user')
def user_detail_verbose(request, username):
    try:
        luser = placard.models.account.objects.get(uid=username)
    except placard.models.account.DoesNotExist:
        raise Http404

    return render_to_response('lusers/user_detail_verbose.html', locals(), context_instance=RequestContext(request))


@permission_required('auth.change_user')   
def users_groups(request, username):
    try:
        luser = placard.models.account.objects.get(uid=username)
    except placard.models.account.DoesNotExist:
        raise Http404

    return render_to_response('lusers/users_groups.html', {'luser': luser}, context_instance=RequestContext(request))

    
