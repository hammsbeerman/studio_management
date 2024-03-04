#import random
from django.http import HttpResponse
from django.shortcuts import render
from django.db.models import Q
from django.template.loader import render_to_string
from workorders.models import Workorder, WorkorderItem
from customers.models import Customer, Contact

#from articles.models import Article


def home_view(request, id=None):
    #article_obj = Article.objects.get(id=1)
    #Get all articles
    #article_list = Article.objects.all()
    #Get articles with a slug field
    
    #article_list = Article.objects.exclude(slug__isnull=True)

    context = {
        
    }
    #HTML_STRING = render_to_string("home.html", context)
    #return HttpResponse(HTML_STRING)
    return render(request, 'home.html', context)

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