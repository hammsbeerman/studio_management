#import random
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
from django.template.loader import render_to_string
from workorders.models import Workorder, WorkorderItem
from customers.models import Customer, Contact
from accounts.decorators import allowed_users
from controls.models import JobStatus, UserGroup
from accounts.models import Profile

#from articles.models import Article

@login_required
def dashboard(request, id=None):
    user = request.user.id
    items = WorkorderItem.objects.filter(assigned_user_id = user).exclude(completed=1).order_by("-workorder")
    #completed = Workorder.objects.all().exclude(workorder=1111).exclude(completed=0).exclude(quote=1).order_by("-workorder")
    #quote = Workorder.objects.all().exclude(workorder=1111).exclude(quote=0).order_by("-workorder")
    status = JobStatus.objects.all()
    print(user)

    #article_obj = Article.objects.get(id=1)
    #Get all articles
    #article_list = Article.objects.all()
    #Get articles with a slug field
    #article_list = Article.objects.exclude(slug__isnull=True)

    context = {
        'items':items,
        'user':user,
        #'workorders': workorder,
        #'completed': completed,
        #'quote': quote,
        'status':status,
    }
    return render(request, "dashboard/employee_dashboard.html", context)


@login_required
def assigned_item_list(request, id=None):
    user = request.user.id
    items = WorkorderItem.objects.filter(assigned_user_id = user).exclude(completed=1).order_by("-workorder")

    context = {
        'items':items,

    }

    return render(request, "dashboard/partials/assigned_item_list.html", context)

@login_required
def design_item_list(request, id=None):
    user = request.user.id
    items = WorkorderItem.objects.filter(job_status_id = 2).exclude(completed=1).order_by("-workorder")

    context = {
        'items':items,
    }
    return render(request, "dashboard/partials/design_item_list.html", context)

@login_required
def selected_item_list(request, id=None):
    item_status = ''
    status = JobStatus.objects.all()
    if request.method == "GET":
        item = request.GET.get('items')
        print(item)
        try:
            item_status = JobStatus.objects.get(id=item)
            items = WorkorderItem.objects.filter(job_status_id = item).exclude(completed=1).order_by("-workorder")
        except:
            item_status = 'Select Job Status'
            items = ''
            pass
    context = {
        'item_status':item_status,
        'items':items,
        'status':status,
    }
    return render(request, "dashboard/partials/selected_item_list.html", context)

@login_required
def group_item_list(request, id=None):
    user = request.user.profile.id
    group = Profile.objects.get(user=user)
    test = group.group.all()
    print(test)
    items = WorkorderItem.objects.filter(assigned_group__profile__user=request.user).exclude(completed=1)
    #for x in test:
    ##items = WorkorderItem.objects.filter(assigned_group_id__exact = test).exclude(completed=1).order_by("-workorder")
    # groups = UserGroup.group_set.all()
    # print(groups)
    # #group = Profile.objects.filter(user=user)
    # group = Profile.objects.get(user_id=user).UserGroup
    # print(group)
    # for x in group:
    #     print(group)
    # print('Group user')
    print(user)
    #items = WorkorderItem.objects.filter(job_status_id = 2).exclude(completed=1).order_by("-workorder")

    context = {
        'items':items,
    }
    return render(request, "dashboard/partials/group_item_list.html", context)

@login_required
def stale_item_list(request, id=None):
    user = request.user.profile.id
    group = Profile.objects.get(user=user)
    test = group.group.all()
    print(test)
    stale_date = timezone.now() - timedelta(days=4)
    print(stale_date)
    items = WorkorderItem.objects.filter(assigned_group__profile__user=request.user).exclude(updated__lt=stale_date).exclude(completed=1)
    #items = WorkorderItem.objects.filter(updated__lt=stale_date)
    #for x in test:
    ##items = WorkorderItem.objects.filter(assigned_group_id__exact = test).exclude(completed=1).order_by("-workorder")
    # groups = UserGroup.group_set.all()
    # print(groups)
    # #group = Profile.objects.filter(user=user)
    # group = Profile.objects.get(user_id=user).UserGroup
    # print(group)
    # for x in group:
    #     print(group)
    # print('Group user')
    print(user)
    #items = WorkorderItem.objects.filter(job_status_id = 2).exclude(completed=1).order_by("-workorder")

    context = {
        'items':items,
    }
    return render(request, "dashboard/partials/stale_item_list.html", context)