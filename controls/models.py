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
    
class InventoryCategory(models.Model):
    name = models.CharField('Name', max_length=100, null = True)

    def __str__(self):
        return self.name
    
class GroupCategory(models.Model):
    name = models.CharField('Name', max_length=100)
    name = models.CharField('Test', max_length=100)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("controls:view_price_group_detail", kwargs={"id": self.id})
    
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
    pricesheet_type = models.ForeignKey(FixedCost, blank=True, null=True, on_delete=models.SET_NULL)
    inventory_category = models.ForeignKey(InventoryCategory, blank=True, null=True, on_delete=models.DO_NOTHING)
    wideformat = models.BooleanField('Wide Format', blank=False, null=True, default=False)
    active = models.BooleanField('Active', blank=True, null=True, default=True)

    def __str__(self):
        return self.name
    
class SubCategory(models.Model):
    category = models.ForeignKey(Category, blank=False, null=True, on_delete=models.SET_NULL, related_name="Category")
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    template = models.BooleanField('Template', blank=True, null=True, default=False)
    set_price = models.BooleanField('Is setprice category', blank=False, null=True, default=False)
    setprice_name = models.CharField('Name', max_length=100, blank=True, null=True)
    inventory_category = models.ForeignKey(InventoryCategory, blank=True, null=True, on_delete=models.DO_NOTHING)
    

    def __str__(self):
        return self.name
    
# class SubSubCategory(models.Model):
#     subcategory = models.ForeignKey(SubCategory, blank=False, null=True, on_delete=models.SET_NULL, related_name="SubCategory")
#     name = models.CharField('Name', max_length=100, blank=True, null=True)
#     description = models.CharField('Description', max_length=100, blank=True, null=True)
#     template = models.BooleanField('Template', blank=True, null=True, default=False)
#     set_price = models.BooleanField('Is setprice category', blank=False, null=True, default=False)
#     setprice_name = models.CharField('Name', max_length=100, blank=True, null=True)
    

#     def __str__(self):
#         return self.name
    
class SetPriceCategory(models.Model):
    category = models.ForeignKey(Category, blank=False, null=True, on_delete=models.SET_NULL)
    name = models.CharField('Name', max_length=100, blank=False, null=False)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = False, blank=True, null=True)

    def __str__(self):
        return self.name

    
class DesignType(models.Model):
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name
    
class PostageType(models.Model):
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name
    

class SetPriceItemPrice(models.Model):
    name = models.ForeignKey(SetPriceCategory, max_length=100, blank=True, null=True, on_delete=models.DO_NOTHING)
    description = models.CharField('Description', max_length=100, blank=False, null=False)
    set_quantity = models.DecimalField('Quantity / Order', max_digits=10, decimal_places=2, blank=False, null=False)
    price = models.DecimalField('Price', max_digits=10, decimal_places=2, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = False, blank=True, null=True)

    def __str__(self):
        return self.description
    
class Measurement(models.Model):
    name = models.CharField('Name', max_length=100, blank=False, null=True)

    def __str__(self):
        return self.name
    
class JobStatus(models.Model):
    name = models.CharField('Name', max_length=100, blank=False, null=True)
    icon = models.ImageField(null=True, blank=True, upload_to="jobstatus/")
    workorder_type = models.BooleanField('Workorder Type', blank=True, null=True, default=False)
    workorder_item_type = models.BooleanField('Workorder Item Type', blank=True, null=True, default=False)

    def __str__(self):
        return self.name
    
class UserGroup(models.Model):
    name = models.CharField('Name', max_length=100, null = True)

    def __str__(self):
        return self.name
    
class PaymentType(models.Model):
    name = models.CharField('Name', max_length=100, null = True)
    detail_field = models.CharField('Detail Field', max_length=100, blank=True, null = True)

    def __str__(self):
        return self.name

class RetailInventoryCategory(models.Model):
    name = models.CharField('Name', max_length=100, null = True)
    icon = models.ImageField(null=True, blank=True, upload_to="retail_category")
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    active = models.BooleanField('Active', blank=True, null=True, default=True)
    parent = models.CharField('Parent Category', max_length=10, null = True)

    def __str__(self):
        return self.name
    
    def get_subcat_url(self):
        return reverse("retail:subcat", kwargs={"cat": self.pk})
    
    def get_parent_url(self):
        return reverse("retail:parent", kwargs={"cat": self.parent})
    
class RetailInventorySubCategory(models.Model):
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    icon = models.ImageField(null=True, blank=True, upload_to="retail_category")
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    inventory_category = models.ManyToManyField(RetailInventoryCategory)
    active = models.BooleanField('Active', blank=True, null=True, default=True)
    

    def __str__(self):
        return self.name

     

    

    
