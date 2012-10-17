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
from django.template import RequestContext, Context, Template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseNotFound, Http404
from django.contrib.auth.decorators import permission_required
from django.template.loader import render_to_string
from django.core.mail import send_mass_mail
from django.contrib import messages

from andsome.forms import EmailForm
from placard.lusers.forms import AddMemberForm
from placard.lgroups.forms import BasicLDAPGroupForm, RenameGroupForm


import tldap
import placard.models

def group_list(request):
    groups = placard.models.group.objects.all()

    return render_to_response('lgroups/group_list.html', {'group_list': groups, 'request': request }, context_instance=RequestContext(request))


def group_detail(request, group_id):
    try:
        group =  placard.models.group.objects.get(gidNumber=group_id)
    except placard.models.group.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        # add member
        form = AddMemberForm(request.POST, group=group)
        if form.is_valid():
            form.save()
            messages.info(request, u'User %s has been added to group %s.' % (user, group))
            return HttpResponseRedirect(reverse("plac_grp_detail",kwargs={ 'group_id': group.gidNumber }))
    else:
        form = AddMemberForm(group=group)

    return render_to_response('lgroups/group_detail.html', locals(), context_instance=RequestContext(request))


@permission_required('auth.change_group')
def remove_member(request, group_id, user_id):
    try:
        group = placard.models.group.objects.get(gidNumber=group_id)
    except placard.models.group.DoesNotExist:
        raise Http404

    try:
        luser = placard.models.account.objects.get(uid=user_id)
    except placard.models.account.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        group.secondary_people.remove(luser)
        messages.info(request, u"User %s removed from group %s" % (luser, group))
        return HttpResponseRedirect(reverse("plac_user_detail",kwargs={ 'username': luser.uid }))

    return render_to_response('lgroups/remove_member.html', locals(), context_instance=RequestContext(request))


@permission_required('auth.add_group')
def add_edit_group(request, group_id=None, form=BasicLDAPGroupForm):
    Form = form

    if group_id is not None:
        try:
            group = placard.models.group.objects.get(gidNumber=group_id)
        except placard.models.group.DoesNotExist:
            raise Http404
    else:
        group = None

    if request.method == 'POST':

        form = Form(request.POST, group=group)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('plac_grp_list'))

    else:
        form = Form(group=group)

    return render_to_response('lgroups/group_form.html', locals(), context_instance=RequestContext(request))
   

@permission_required('auth.delete_group')
def delete_group(request, group_id):
    try:
        group = placard.models.group.objects.get(gidNumber=group_id)
    except placard.models.group.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        group.delete()
        return HttpResponseRedirect(reverse('plac_grp_list'))
    
    return render_to_response('lgroups/group_confirm_delete.html', locals(), context_instance=RequestContext(request))


@permission_required('auth.delete_group')
def group_detail_verbose(request, group_id):
    try:
        group =  placard.models.group.objects.get(gidNumber=group_id)
    except exceptions.DoesNotExistException:
        raise Http404

    return render_to_response('lgroups/group_detail_verbose.html', locals(), context_instance=RequestContext(request))


def send_members_email(request, group_id):
    try:
        group =  placard.models.group.objects.get(gidNumber=group_id)
    except exceptions.DoesNotExistException:
        raise Http404

    def list_all_people():
        for i in group.primary_accounts.all():
            yield i
        for i in group.secondary_people.all():
            yield i

    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            subject_t, body_t = form.get_data()
            members = list_all_people()
            emails = []
            for member in members:
                if member.mail is not None:
                    ctx = Context({
                            'first_name': member.givenName,
                            'last_name': member.sn,
                            })
                    subject = Template(subject_t).render(ctx)
                    body = Template(body_t).render(ctx)
                    emails.append((subject, body, settings.DEFAULT_FROM_EMAIL, [member.mail]))
            if emails:
                send_mass_mail(emails)
            return HttpResponseRedirect(reverse("plac_grp_detail",kwargs={ 'group_id': group.gidNumber }))
    else:
        form = EmailForm()

    return render_to_response('lgroups/send_email_form.html', {'form': form, 'group': group}, context_instance=RequestContext(request))


@permission_required('auth.change_group')
def rename_group(request, group_id):
    try:
        group =  placard.models.group.objects.get(gidNumber=group_id)
    except exceptions.DoesNotExistException:
        raise Http404

    if request.method == 'POST':
        form = RenameGroupForm(request.POST, group=group)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("plac_grp_detail",kwargs={ 'group_id': group.gidNumber }))
    else:
        form = RenameGroupForm(group=group)
    return render_to_response('lgroups/group_rename.html', {'form': form}, context_instance=RequestContext(request))
