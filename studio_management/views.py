#import random
from django.http import HttpResponse
from django.template.loader import render_to_string
#from articles.models import Article


def home_view(request, id=None):
    #article_obj = Article.objects.get(id=1)
    #Get all articles
    #article_list = Article.objects.all()
    #Get articles with a slug field
    
    #article_list = Article.objects.exclude(slug__isnull=True)

    context = {
        
    }
    HTML_STRING = render_to_string("home.html", context)
    return HttpResponse(HTML_STRING)