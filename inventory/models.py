from django.db import models
from django.urls import reverse

class Inventory(models.Model):
    category = models.ForeignKey(Category, blank=False, null=True, on_delete=models.CASCADE)
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    unit_cost = 
    current_stock = 
    vendor = 
    color = 
    size = 
    measurement = 
    date_updated = 