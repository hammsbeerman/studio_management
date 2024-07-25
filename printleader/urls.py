from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    printleader_history,
    printleader_history_detail
    #setprice_list,
)

app_name='printleader'

urlpatterns = [
    path('printleader_history/', printleader_history, name='printleader_history'),
    path('printleader_history_detail/', printleader_history_detail, name='printleader_history_detail'),
    #path('setprice_list/', setprice_list, name='setprice_list'),
]