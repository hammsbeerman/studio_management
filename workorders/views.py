from django.shortcuts import render

def create_base(request):
    return render(request, "workorders/create.html",)