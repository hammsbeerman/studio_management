from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from .forms import KruegerJobDetailForm
from workorders.forms import WorkorderNewItemForm
from .models import KruegerJobDetail, PaperStock
from workorders.models import WorkorderItem, Category, Workorder


def newjob(request, id, pk):
    workorder = id
    item = pk
    print(workorder)
    print(item)
    obj = WorkorderItem.objects.get(id=item)
    description = obj.description
    jobitem = KruegerJobDetail.objects.get(workorder_item=item)
    #print(jobitem.workorder_id)
    jobobj = jobitem.id
    jobid = jobobj
    obj = get_object_or_404(KruegerJobDetail, id=jobobj)
    form = KruegerJobDetailForm(instance=obj)
    #print(obj.__dict__)
    internal_company = form.instance.internal_company
    selected_paper = form.instance.paper_stock_id
    try:
        selected_paper = PaperStock.objects.get(id=selected_paper)
        print(selected_paper.description)
        print(selected_paper)
    except: 
        selected_paper = ''
    formdata = KruegerJobDetail.objects.get(id=jobid)
    print(formdata)
    #selected_paper = formdata.paper_stock.description
    papers = PaperStock.objects.all()
    #print(form.instance.internal_company)
    obj = Workorder.objects.get(workorder=workorder)
    print('workorder')
    print(obj.id)
    workorder_id = obj.id
    #print(form.instance.paper_stock_id)
    #print(form.instance.paper_stock_id)
    #print(formdata.paper_stock_id)
    #print(selected_paper)
    if request.method == "POST":
        # print('poster')
        jobid = request.POST.get('jobid')
        workorderid = request.POST.get('workorder')
        obj = get_object_or_404(KruegerJobDetail, pk=jobid)
        form = KruegerJobDetailForm(request.POST, instance=obj)
        #print(form.cleaned_data)
        papers = PaperStock.objects.all()
        obj = Workorder.objects.get(workorder=workorder)
        workorder = obj.workorder
        print('workorder')
        # print(obj.workorder)
        print(workorderid)
        #print(obj.__dict__)
        print('endworkorder')
        form.instance.workorder_item = item
        #form.instance.workorder_id = workorderid
        form.instance.hr_workorder = obj.workorder
        form.instance.company = obj.internal_company
        form.instance.customer_id = obj.customer_id
        form.instance.hr_customer = obj.hr_customer
        if form.is_valid():
            lineitem = WorkorderItem.objects.get(id=item)
            lineitem.description = form.instance.description
            print(lineitem.description)
            lineitem.save()
            form.save()
            print(form.errors)
            messages.success(request, 'Successfully Saved')
            return redirect('workorders:overview', id=obj.workorder)
        else:
            print(form.errors)
    context = {
        "form": form,
        "description": description,
        "title": "New Job",
        'jobid':jobid,
        'papers': papers,
        'formdata':formdata,
        'internal_company':internal_company,
        'selected_paper':selected_paper,
        'workorder_id': workorder_id
        #'papersizes': papersizes,
    }
    return render(request, "krueger/pricingforms/bigform.html", context)


def paperprice(request):
    paper = request.GET.get('paper_stock')
    #print(paper)
    paperprices = PaperStock.objects.filter(pk=paper)
    context = {'paperprices': paperprices}
    return render(request, 'krueger/partials/paperstockprice.html', context)

@ require_POST
def remove_workorder_item(request):
    jobid = request.POST.get('jobid')
    print(jobid)
    #print(pk)
    jobitem = KruegerJobDetail.objects.get(id=jobid)
    print(jobitem.id)#8
    lineitem = jobitem.workorder_item
    workorder = jobitem.hr_workorder
    print(workorder)#5090
    print(lineitem)#174
    job = get_object_or_404(KruegerJobDetail, pk=jobid)
    print('jobdetail')
    print(job)
    job.delete()
    line = get_object_or_404(WorkorderItem, pk=lineitem)
    print('lineitem')
    print(lineitem)
    line.delete()
    print(workorder)
    #return redirect("workorders:overview", id=workorder)
    #return render(request, 'workorders/overview.html')
    url = reverse('workorders:overview', kwargs={'id': workorder})
    return HttpResponseRedirect(url)