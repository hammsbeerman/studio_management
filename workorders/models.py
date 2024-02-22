from django.db import models
from django.urls import reverse
from customers.models import Customer, Contact
from controls.models import Category, SubCategory, DesignType, SetPriceItem, SetPriceItemPrice


class Workorder(models.Model):
    customer = models.ForeignKey(Customer, blank=False, null=False, on_delete=models.CASCADE, related_name='workorders')
    contact = models.ForeignKey(Contact, blank=True, null=True, on_delete=models.SET_NULL)
    hr_customer = models.CharField('Customer Name', max_length=100, blank=True, null=True,)
    hr_contact = models.CharField('Contact Name', max_length=100, blank=True, null=True,)
    ##company = models.OneToOneField(Customer, on_delete=models.CASCADE, blank=True, null=True)
    workorder = models.CharField('Workorder', max_length=100, blank=False, null=False, unique=True)
    internal_company = models.CharField('Internal Company', choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing')], max_length=100, blank=False, null=False)
    quote = models.CharField('Quote', choices=[('1', 'Quote'), ('0', 'Workorder')], max_length=100, blank=False, null=False)
    quote_number = models.CharField('Quote Number', max_length=100, blank=True, null=True)
    description = models.CharField('Description', max_length=100, blank=True, null=True)
    deadline = models.DateField('Deadline', blank=True, null=True)
    po_number = models.CharField('PO Number', max_length=100, blank=True, null=True)
    budget = models.CharField('Budget', max_length=100, blank=True, null=True)
    quoted_price = models.CharField('Quoted Price', max_length=100, blank=True, null=True)
    original_order = models.PositiveSmallIntegerField('Original Order', blank=True, null=True)
    notes = models.TextField('Notes:', blank=True, null=False)
    lk_workorder = models.CharField('LK Workorder', max_length=100, blank=True, null=True)
    printleader_workorder = models.CharField('Printleader', max_length=100, blank=True, null=True)
    #total_price = models.IntegerField('Total Price', blank=True, default=True)
    billed = models.BooleanField('Billed', blank=False, null=False, default=False)
    tax_exempt = models.BooleanField(default=False)
    percent_discount = models.CharField('Discount %', max_length=100, blank=True, null=True)
    dollar_discount = models.CharField('Discount $', max_length=100, blank=True, null=True)
    tax = models.CharField('Tax', max_length=100, blank=True, null=True)
    subtotal = models.CharField('Subtotal', max_length=100, blank=True, null=True)
    workorder_total = models.CharField('Workorder Total', max_length=100, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)
    completed = models.BooleanField(blank=False, null=False, default=False)

    def get_absolute_url(self):
        return reverse("workorders:overview", kwargs={"id": self.workorder})
    
    def get_history_url(self):
        return reverse("workorders:history_overview", kwargs={"id": self.workorder})
    
    def get_item_url(self):
        return reverse("workorders:workorder_item_list", kwargs={"id": self.workorder})
    
    def __str__(self):
        return self.workorder


class WorkorderItem(models.Model):
    workorder = models.ForeignKey(Workorder, blank=False, null=True, on_delete=models.CASCADE)
    workorder_hr = models.CharField('Workorder Human Readable', max_length=100, blank=False, null=False)
    item_category = models.ForeignKey(Category, blank=True, null=True, on_delete=models.CASCADE)
    item_subcategory = models.ForeignKey(SubCategory, blank=True, null=True, on_delete=models.SET_NULL)
    setprice_category = models.ForeignKey(SetPriceItem, blank=True, null=True, on_delete=models.SET_NULL)
    setprice_item = models.ForeignKey(SetPriceItemPrice, blank=True, null=True, on_delete=models.SET_NULL) 
    #item_subcategory = models.CharField('Subcategory', max_length=100, blank=True, null=True)
    pricesheet_modified = models.BooleanField('Pricesheet Modified', blank=True, null=True, default=False)
    design_type = models.ForeignKey(DesignType, blank=True, null=True, on_delete=models.CASCADE)
    description = models.CharField('Description', max_length=100, blank=False, null=False)
    item_order = models.PositiveSmallIntegerField('Display Order', blank=True, null=True)
    quantity = models.DecimalField('Quantity', max_digits=6, decimal_places=2, blank=True, null=True)
    unit_price = models.DecimalField('Unit Price', max_digits=10, decimal_places=4, blank=True, null=True)
    total_price = models.DecimalField('Total Price', max_digits=8, decimal_places=2, blank=True, null=True)
    override_price = models.DecimalField('Override Price', max_digits=8, decimal_places=2, blank=True, null=True)
    absolute_price = models.DecimalField('Absolute Price', max_digits=8, decimal_places=2, blank=True, null=True)
    last_item_order = models.CharField('Original Item Order', max_length=100, blank=True, null=True)
    last_item_price = models.CharField('Original Item Price', max_length=100, blank=True, null=True)
    billable = models.BooleanField(default=True)
    notes = models.TextField('Notes:', blank=True, null=False)
    internal_company = models.CharField('Internal Company', choices=[('LK Design', 'LK Design'), ('Krueger Printing', 'Krueger Printing')], max_length=100, blank=False, null=False)
    tax_exempt = models.BooleanField(default=False)
    tax_amount = models.DecimalField('Tax Amount', max_digits=8, decimal_places=2, blank=True, null=True)
    total_with_tax = models.DecimalField('Total', max_digits=8, decimal_places=2, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    updated = models.DateTimeField(auto_now = True, blank=False, null=False)

    def get_absolute_url(self):
        return self.workorder.get_absolute_url()
    
    def edit_print_item_url(self):
        #return reverse("krueger:bigform", kwargs={"id": self.workorder})
        return reverse("krueger:bigform", kwargs={"id": self.workorder, "pk":self.pk})
    
    def edit_template_item_url(self):
        #return reverse("krueger:bigform", kwargs={"id": self.workorder})
        return reverse("pricesheet:edititem", kwargs={"id": self.workorder_id, "pk":self.pk, "cat":self.item_category_id,})
    
    #def get_workorder_add(self):
    #    return reverse("workorders:detail", kwargs={"id": self.workorder})

    def get_workorder_add_url(self):
        kwargs = {
            "parent_id": self.workorder.id,
            "id": self.id
        }
        return reverse("workorders:add", kwargs=kwargs)
    
    def get_hx_edit_url(self):
        kwargs = {
            "parent_id": self.workorder.id,
            "id": self.id
        }
        return reverse("workorders:hx-workorder-item-detail", kwargs=kwargs)

    #def __str__(self):
    #    return self.description

    # @property
    # def get_total_price(self):
    #     return sum([food.carbs for food in self.foods.all()])


    def __str__(self):
        return self.workorder.workorder #+ ' -- ' + self.description
    
    