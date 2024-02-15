from django.db import models
from django.urls import reverse

class Numbering(models.Model):
    name = models.CharField('Name', max_length=100, blank=False, null=False, unique=True)
    value = models.PositiveIntegerField('Value', blank=False, null=False)

    def __str__(self):
        return self.name
    
class FixedCost(models.Model):
    name = models.CharField('Name', max_length=100, blank=False, null=False, unique=True)
    create_workorder = models.DecimalField('Create Workordeer', max_digits=10, decimal_places=2, blank=True, null=True)
    reclaim_artwork =  models.DecimalField('Reclaim Artwork', max_digits=10, decimal_places=2, blank=True, null=True)
    send_to_press =  models.DecimalField('Send to press', max_digits=10, decimal_places=2, blank=True, null=True)
    send_mailmerge_to_press =  models.DecimalField('Send Mailmerge to press', max_digits=10, decimal_places=2, blank=True, null=True)
    material_markup = models.DecimalField('Material Markup Percentage', max_digits=10, decimal_places=2, blank=True, null=True)
    wear_and_tear =  models.DecimalField('Wear and Tear', max_digits=10, decimal_places=2, blank=True, null=True)
    trim_to_size =  models.DecimalField('Trim to Size', max_digits=10, decimal_places=2, blank=True, null=True)
    ##
    duplo_1 =  models.DecimalField('Duplo1', max_digits=10, decimal_places=2, blank=True, null=True)
    duplo_2 =  models.DecimalField('Duplo2', max_digits=10, decimal_places=2, blank=True, null=True)
    duplo_3 =  models.DecimalField('Duplo3', max_digits=10, decimal_places=2, blank=True, null=True)
    #
    ncr_compound =  models.DecimalField('NCR Compound', max_digits=10, decimal_places=2, blank=True, null=True)
    pad_compound =  models.DecimalField('Padding Compound', max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.name
    
class Category(models.Model):
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    design_type = models.BooleanField('Design Type', blank=True, null=True)

    formname = models.CharField('Form', max_length=100, blank=True, null=True)
    modelname = models.CharField('Model', max_length=100, blank=True, null=True)
    modal = models.BooleanField('Popup Modal', blank=True, null=True, default=False)
    setprice = models.BooleanField('Is setprice category', blank=False, null=True, default=False)
    material_type = models.CharField('Material Type', max_length=100, blank=True, null=True)
    template = models.BooleanField('Template', blank=True, null=True, default=False)
    customform = models.BooleanField('Uses Custom Form', blank=True, null=True, default=False)
    pricesheet_type = models.ForeignKey(FixedCost, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class SubCategory(models.Model):
    category = models.ForeignKey(Category, blank=False, null=True, on_delete=models.CASCADE, related_name="Category")
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    template = models.BooleanField('Template', blank=True, null=True, default=False)
    set_price = models.BooleanField('Is setprice category', blank=False, null=True, default=False)
    setprice_name = models.CharField('Name', max_length=100, blank=True, null=True)
    

    def __str__(self):
        return self.name
    
class SetPriceItem(models.Model):
    category = models.ForeignKey(Category, blank=False, null=True, on_delete=models.CASCADE)
    name = models.CharField('Name', max_length=100, blank=False, null=False)

    def __str__(self):
        return self.name

    
class DesignType(models.Model):
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name
    

class SetPriceItemPrice(models.Model):
    name = models.ForeignKey(SetPriceItem, max_length=100, blank=True, null=True, on_delete=models.DO_NOTHING)
    description = models.CharField('Description', max_length=100, blank=False, null=False)
    set_quantity = models.DecimalField('Quantity / Order', max_digits=10, decimal_places=2, blank=False, null=False)
    price = models.DecimalField('Price', max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.description
    
class Measurement(models.Model):
    name = name = models.CharField('Name', max_length=100, blank=False, null=True)

    def __str__(self):
        return self.name