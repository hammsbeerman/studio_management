#import random
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from django.template.loader import render_to_string
from workorders.models import Workorder, WorkorderItem
from customers.models import Customer, Contact

#from articles.models import Article

@login_required
def home_view(request, id=None):
    user = request.user.id
    items = WorkorderItem.objects.filter(assigned_user_id = user).exclude(completed=1).order_by("-workorder")
    completed = Workorder.objects.all().exclude(workorder=1111).exclude(completed=0).exclude(quote=1).order_by("-workorder")
    quote = Workorder.objects.all().exclude(workorder=1111).exclude(quote=0).order_by("-workorder")
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
        'completed': completed,
        'quote': quote,
    }
    #HTML_STRING = render_to_string("home.html", context)
    #return HttpResponse(HTML_STRING)
    return render(request, 'home.html', context)

@login_required
def search(request):
    q = request.GET.get('q')
    workorders = Workorder.objects.filter(
        Q(hr_customer__icontains=q) | Q(workorder__icontains=q) | Q(description__icontains=q)
          ).distinct()
    workorder_item = WorkorderItem.objects.filter(description__icontains=q).distinct()
    customer = Customer.objects.filter(
        Q(company_name__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    #contact = Contact.objects.filter(fname__icontains=q)
    context = {
        'workorders':workorders,
        'workorder_item':workorder_item,
        'customer':customer,
        #'contact':contact,
    }
    return render(request, 'search.html', context)

@login_required
def assigned_item_list(request, id=None):
    user = request.user.id
    items = WorkorderItem.objects.filter(assigned_user_id = user).exclude(completed=1).order_by("-workorder")

    context = {
        'items':items,

    }

    return render(request, "main/partials/assigned_item_list.html", context)

@login_required
def design_item_list(request, id=None):
    user = request.user.id
    items = WorkorderItem.objects.filter(job_status_id = 2).exclude(completed=1).order_by("-workorder")

    context = {
        'items':items,
    }
    return render(request, "main/partials/design_item_list.html", context)