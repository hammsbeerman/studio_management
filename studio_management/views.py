#import random
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Q
from django.template.loader import render_to_string
from workorders.models import Workorder, WorkorderItem
from customers.models import Customer, Contact
from accounts.decorators import allowed_users
from controls.models import JobStatus

#from articles.models import Article

@login_required
def home_view(request, id=None):
    # user = request.user.id
    # items = WorkorderItem.objects.filter(assigned_user_id = user).exclude(completed=1).order_by("-workorder")
    # #completed = Workorder.objects.all().exclude(workorder=1111).exclude(completed=0).exclude(quote=1).order_by("-workorder")
    # #quote = Workorder.objects.all().exclude(workorder=1111).exclude(quote=0).order_by("-workorder")
    # status = JobStatus.objects.all()
    # print(user)

    #article_obj = Article.objects.get(id=1)
    #Get all articles
    #article_list = Article.objects.all()
    #Get articles with a slug field
    #article_list = Article.objects.exclude(slug__isnull=True)

    #context = {
        # 'items':items,
        # 'user':user,
        # #'workorders': workorder,
        # #'completed': completed,
        # #'quote': quote,
        # 'status':status,
    #}
    #HTML_STRING = render_to_string("home.html", context)
    #return HttpResponse(HTML_STRING)
    #return render(request, 'home.html', context)

    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    else:
        return redirect('accounts/login')

@login_required
def search(request):
    q = request.GET.get('q')
    workorders = Workorder.objects.filter(
        Q(hr_customer__icontains=q) | Q(workorder__icontains=q) | Q(description__icontains=q) |
        Q(lk_workorder__icontains=q) | Q(printleader_workorder__icontains=q) |
        Q(kos_workorder__icontains=q) | Q(workorder_total__icontains=q)
          ).distinct()
    open = workorders.filter(paid_in_full=0).exclude(completed=0)
    workorder_item = WorkorderItem.objects.filter(description__icontains=q).distinct()
    customer = Customer.objects.filter(
        Q(company_name__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        ).distinct()
    contact = Contact.objects.filter(
        Q(fname__icontains=q) | Q(lname__icontains=q)
    ).distinct()
    #contact = Contact.objects.filter(fname__icontains=q)
    context = {
        'workorders':workorders,
        'open':open,
        'workorder_item':workorder_item,
        'customer':customer,
        'contact':contact,
    }
    return render(request, 'search.html', context)

def username(request):
    # user = request.user.logged_in
    # logged = Profile.objects.get(user=user)
    test = 'test123'
    context = {
        'test':test
    }
    return render(request, 'navbar.html', context)

# @login_required
# def assigned_item_list(request, id=None):
#     user = request.user.id
#     items = WorkorderItem.objects.filter(assigned_user_id = user).exclude(completed=1).order_by("-workorder")

#     context = {
#         'items':items,

#     }

#     return render(request, "dashboard/partials/assigned_item_list.html", context)

# @login_required
# def design_item_list(request, id=None):
#     user = request.user.id
#     items = WorkorderItem.objects.filter(job_status_id = 2).exclude(completed=1).order_by("-workorder")

#     context = {
#         'items':items,
#     }
#     return render(request, "dashboard/partials/design_item_list.html", context)

# @login_required
# def selected_item_list(request, id=None):
#     item_status = ''
#     status = JobStatus.objects.all()
#     if request.method == "GET":
#         item = request.GET.get('items')
#         print(item)
#         item_status = JobStatus.objects.get(id=item)
#         items = WorkorderItem.objects.filter(job_status_id = item).exclude(completed=1).order_by("-workorder")
#     context = {
#         'item_status':item_status,
#         'items':items,
#         'status':status,
#     }
#     return render(request, "dashboard/partials/selected_item_list.html", context)