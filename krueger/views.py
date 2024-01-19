from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from .forms import KruegerJobDetailForm
from .models import KruegerJobDetail, PaperStock

def newjob(request):
    form = KruegerJobDetailForm(request.POST or None)
    total_invoices = KruegerJobDetail.objects.count()
    #Following for HTMX Paper price
    papers = PaperStock.objects.all()
    #paper = request.GET.get('paper_stock')
    #print(paper)
    #papersizes = PaperStock.objects.filter(pk=paper)
    #Following is for sidebar, to be implemented in the future
    #queryset = KruegerJobDetail.objects.filter(company='LK').order_by('-dateentered')[:6]
    if form.is_valid():
        print(form.cleaned_data)
        form.save()
        messages.success(request, 'Successfully Saved')
        return redirect('/krueger')
    context = {
        "form": form,
        "title": "New Job",
        "total_invoices": total_invoices,
		#"queryset": queryset,
        'papers': papers,
        #'papersizes': papersizes,
    }
    return render(request, "krueger/pricingforms/bigform.html", context)

def paperprice(request):
    paper = request.GET.get('paper_stock')
    #print(paper)
    paperprices = PaperStock.objects.filter(pk=paper)
    context = {'paperprices': paperprices}
    return render(request, 'krueger/partials/paperstockprice.html', context)
