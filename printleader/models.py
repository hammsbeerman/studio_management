from django.db import models

class PrintleaderHistory(models.Model):
    printleader_invoice = models.CharField('Printleader Invoice', max_length=100, blank=True, null=True)
    customer = models.CharField('Customer', max_length=100, blank=True, null=True)
    printleader_customer_number = models.CharField('Printleader Customer Number', max_length=100, blank=True, null=True)
    invoice_date = models.DateField(auto_now = False, blank=True, null=True)
    nontaxable_amount = models.CharField('Non taxable amount', max_length=100, blank=True, null=True)
    taxable_amount = models.CharField('Taxable Amount', max_length=100, blank=True, null=True)
    tax_amount = models.CharField('Tax', max_length=100, blank=True, null=True)
    invoice_total = models.CharField('Invoice Total', max_length=100, blank=True, null=True)

class PrintleaderHighLevel(models.Model):
    printleader_invoice = models.CharField('Printleader Invoice', max_length=100, blank=True, null=True)
    customer = models.CharField('Customer', max_length=100, blank=True, null=True)
    printleader_customer_number = models.CharField('Printleader Customer Number', max_length=100, blank=True, null=True)
    printleader_job_name = models.CharField('Printleader Job Name', max_length=100, blank=True, null=True)
    

class PrintleaderARINVODA(models.Model):
    InvoiceNum = models.CharField(max_length=100, null=True, blank=True, verbose_name='InvoiceNum')
    Lineno = models.CharField(max_length=100, null=True, blank=True, verbose_name='Lineno')
    Linetype = models.CharField(max_length=100, null=True, blank=True, verbose_name='Linetype')
    Chgcode = models.CharField(max_length=100, null=True, blank=True, verbose_name='Chgcode')
    Descript = models.CharField(max_length=100, null=True, blank=True, verbose_name='Descript')
    Acctnum = models.CharField(max_length=100, null=True, blank=True, verbose_name='Acctnum')
    Qty = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qty')
    Percost = models.CharField(max_length=100, null=True, blank=True, verbose_name='Percost')
    Fpercost = models.CharField(max_length=100, null=True, blank=True, verbose_name='Fpercost')
    Price = models.CharField(max_length=100, null=True, blank=True, verbose_name='Price')
    Fprice = models.CharField(max_length=100, null=True, blank=True, verbose_name='Fprice')
    Taxable = models.CharField(max_length=100, null=True, blank=True, verbose_name='Taxable')
    Commable = models.CharField(max_length=100, null=True, blank=True, verbose_name='Commable')
    Extension = models.CharField(max_length=100, null=True, blank=True, verbose_name='Extension')
    Fextension = models.CharField(max_length=100, null=True, blank=True, verbose_name='Fextension')
    Items = models.CharField(max_length=100, null=True, blank=True, verbose_name='Items')
    Job_Category = models.CharField(max_length=100, null=True, blank=True, verbose_name='Job Category')
    Jobname = models.CharField(max_length=100, null=True, blank=True, verbose_name='Jobname')
    Jnlbatch = models.CharField(max_length=100, null=True, blank=True, verbose_name='Jnlbatch')
    Itemnum = models.CharField(max_length=100, null=True, blank=True, verbose_name='Itemnum')
    Discount = models.CharField(max_length=100, null=True, blank=True, verbose_name='Discount')
    Discperc = models.CharField(max_length=100, null=True, blank=True, verbose_name='Discperc')
    Press = models.CharField(max_length=100, null=True, blank=True, verbose_name='Press')
    Pss1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Pss1')
    Pss2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Pss2')
    Setupt1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Setupt1')
    Setupt2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Setupt2')
    Stock = models.CharField(max_length=100, null=True, blank=True, verbose_name='Stock')
    Size = models.CharField(max_length=100, null=True, blank=True, verbose_name='Size')
    Blackink = models.CharField(max_length=100, null=True, blank=True, verbose_name='Blackink')
    Pplates = models.CharField(max_length=100, null=True, blank=True, verbose_name='Pplates')
    Side12 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Side12')
    Numoflots = models.CharField(max_length=100, null=True, blank=True, verbose_name='Numoflots')
    Outs = models.CharField(max_length=100, null=True, blank=True, verbose_name='Outs')
    Units = models.CharField(max_length=100, null=True, blank=True, verbose_name='Units')
    Diflev1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Diflev1')
    Diflev2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Diflev2')
    Presstime = models.CharField(max_length=100, null=True, blank=True, verbose_name='Presstime')
    Act_time = models.CharField(max_length=100, null=True, blank=True, verbose_name='Act_time')
    Sheets = models.CharField(max_length=100, null=True, blank=True, verbose_name='Sheets')
    Impres = models.CharField(max_length=100, null=True, blank=True, verbose_name='Impres')
    Overmanual = models.CharField(max_length=100, null=True, blank=True, verbose_name='Overmanual')
    Overs = models.CharField(max_length=100, null=True, blank=True, verbose_name='Overs')
    Pass1s = models.CharField(max_length=100, null=True, blank=True, verbose_name='Pass1s')
    Pass2s = models.CharField(max_length=100, null=True, blank=True, verbose_name='Pass2s')
    Vp = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vp')
    Vpw = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vpw')
    Vpl = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vpl')
    Vfw = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vfw')
    Vfl = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vfl')
    Press_w = models.CharField(max_length=100, null=True, blank=True, verbose_name='Press_w')
    Press_l = models.CharField(max_length=100, null=True, blank=True, verbose_name='Press_l')
    Vppl = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vppl')
    Inkside1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Inkside1')
    Inkside2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Inkside2')
    Workturn = models.CharField(max_length=100, null=True, blank=True, verbose_name='Workturn')
    Margin = models.CharField(max_length=100, null=True, blank=True, verbose_name='Margin')
    Trimtype = models.CharField(max_length=100, null=True, blank=True, verbose_name='Trimtype')
    Schedule = models.CharField(max_length=100, null=True, blank=True, verbose_name='Schedule')
    Sizen = models.CharField(max_length=100, null=True, blank=True, verbose_name='Sizen')
    Jobtype = models.CharField(max_length=100, null=True, blank=True, verbose_name='Jobtype')
    Unitprice = models.CharField(max_length=100, null=True, blank=True, verbose_name='Unitprice')
    Depttime = models.CharField(max_length=100, null=True, blank=True, verbose_name='Depttime')
    Stockqty = models.CharField(max_length=100, null=True, blank=True, verbose_name='Stockqty')
    Stockprice = models.CharField(max_length=100, null=True, blank=True, verbose_name='Stockprice')
    Cutype = models.CharField(max_length=100, null=True, blank=True, verbose_name='Cutype')
    Jobitem = models.CharField(max_length=100, null=True, blank=True, verbose_name='Jobitem')
    Deptstot = models.CharField(max_length=100, null=True, blank=True, verbose_name='Deptstot')
    Item_Description = models.CharField(max_length=100, null=True, blank=True, verbose_name='Item Description')
    Vendponum = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vendponum')
    Vendmarkup = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vendmarkup')
    Vendcostpu = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vendcostpu')
    Salepaper = models.CharField(max_length=100, null=True, blank=True, verbose_name='Salepaper')
    Salelabor = models.CharField(max_length=100, null=True, blank=True, verbose_name='Salelabor')
    Costpaper = models.CharField(max_length=100, null=True, blank=True, verbose_name='Costpaper')
    Costlabor = models.CharField(max_length=100, null=True, blank=True, verbose_name='Costlabor')
    Profpaper = models.CharField(max_length=100, null=True, blank=True, verbose_name='Profpaper')
    Proflabor = models.CharField(max_length=100, null=True, blank=True, verbose_name='Proflabor')
    Platesale = models.CharField(max_length=100, null=True, blank=True, verbose_name='Platesale')
    Platecost = models.CharField(max_length=100, null=True, blank=True, verbose_name='Platecost')
    Profplate = models.CharField(max_length=100, null=True, blank=True, verbose_name='Profplate')
    Matcost = models.CharField(max_length=100, null=True, blank=True, verbose_name='Matcost')
    Labcost = models.CharField(max_length=100, null=True, blank=True, verbose_name='Labcost')
    Done = models.CharField(max_length=100, null=True, blank=True, verbose_name='Done')
    Orditem = models.CharField(max_length=100, null=True, blank=True, verbose_name='Orditem')
    Grain = models.CharField(max_length=100, null=True, blank=True, verbose_name='Grain')
    Isparent = models.CharField(max_length=100, null=True, blank=True, verbose_name='Isparent')
    Cuts = models.CharField(max_length=100, null=True, blank=True, verbose_name='Cuts')
    Usecuts = models.CharField(max_length=100, null=True, blank=True, verbose_name='Usecuts')
    Qty1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qty1')
    Qty2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qty2')
    Qty3 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qty3')
    Qty4 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qty4')
    Qty5 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qty5')
    Qty6 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qty6')
    Orddate = models.CharField(max_length=100, null=True, blank=True, verbose_name='Orddate')
    Grain1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Grain1')
    Mouts = models.CharField(max_length=100, null=True, blank=True, verbose_name='Mouts')
    Prttable = models.CharField(max_length=100, null=True, blank=True, verbose_name='Prttable')
    Itemlink = models.CharField(max_length=100, null=True, blank=True, verbose_name='Itemlink')
    Pricem = models.CharField(max_length=100, null=True, blank=True, verbose_name='Pricem')
    Action = models.CharField(max_length=100, null=True, blank=True, verbose_name='Action')
    Overcopy = models.CharField(max_length=100, null=True, blank=True, verbose_name='Overcopy')
    Project = models.CharField(max_length=100, null=True, blank=True, verbose_name='Project')
    Plevel = models.CharField(max_length=100, null=True, blank=True, verbose_name='Plevel')
    Numofons = models.CharField(max_length=100, null=True, blank=True, verbose_name='Numofons')
    Useons = models.CharField(max_length=100, null=True, blank=True, verbose_name='Useons')
    Plate12 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Plate12')
    Passink1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Passink1')
    Passink2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Passink2')
    Forecast = models.CharField(max_length=100, null=True, blank=True, verbose_name='Forecast')
    Foreperc = models.CharField(max_length=100, null=True, blank=True, verbose_name='Foreperc')
    Shpqty = models.CharField(max_length=100, null=True, blank=True, verbose_name='Shpqty')
    Shpprt = models.CharField(max_length=100, null=True, blank=True, verbose_name='Shpprt')
    Orgstat = models.CharField(max_length=100, null=True, blank=True, verbose_name='Orgstat')
    Worktumb = models.CharField(max_length=100, null=True, blank=True, verbose_name='Worktumb')
    Waste1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Waste1')
    Waste2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Waste2')
    Press2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Press2')
    Overcop2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Overcop2')
    Unitpric2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Unitpric2')
    Attached = models.CharField(max_length=100, null=True, blank=True, verbose_name='Attached')
    Packprt = models.CharField(max_length=100, null=True, blank=True, verbose_name='Packprt')
    Premium = models.CharField(max_length=100, null=True, blank=True, verbose_name='Premium')
    Overperm = models.CharField(max_length=100, null=True, blank=True, verbose_name='Overperm')
    Overhour = models.CharField(max_length=100, null=True, blank=True, verbose_name='Overhour')
    Hourly = models.CharField(max_length=100, null=True, blank=True, verbose_name='Hourly')
    Hourly2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Hourly2')

    def __str__(self):
        return self.InvoiceNum


class PrintleaderSOORDEDT(models.Model):
    OrderNum = models.CharField(max_length=100, null=True, blank=True, verbose_name='OrderNum')
    Type = models.CharField(max_length=100, null=True, blank=True, verbose_name='Type')
    Keyid = models.CharField(max_length=100, null=True, blank=True, verbose_name='Keyid')
    Linetype = models.CharField(max_length=100, null=True, blank=True, verbose_name='Linetype')
    Whcode = models.CharField(max_length=100, null=True, blank=True, verbose_name='Whcode')
    Itemnum = models.CharField(max_length=100, null=True, blank=True, verbose_name='Itemnum')
    Descript = models.CharField(max_length=100, null=True, blank=True, verbose_name='Descript')
    Acctnum = models.CharField(max_length=100, null=True, blank=True, verbose_name='Acctnum')
    Invacct = models.CharField(max_length=100, null=True, blank=True, verbose_name='Invacct')
    Cosacct = models.CharField(max_length=100, null=True, blank=True, verbose_name='Cosacct')
    Commable = models.CharField(max_length=100, null=True, blank=True, verbose_name='Commable')
    Taxable = models.CharField(max_length=100, null=True, blank=True, verbose_name='Taxable')
    Discount = models.CharField(max_length=100, null=True, blank=True, verbose_name='Discount')
    Discperc = models.CharField(max_length=100, null=True, blank=True, verbose_name='Discperc')
    Backorder = models.CharField(max_length=100, null=True, blank=True, verbose_name='Backorder')
    Dropship = models.CharField(max_length=100, null=True, blank=True, verbose_name='Dropship')
    Kitnum = models.CharField(max_length=100, null=True, blank=True, verbose_name='Kitnum')
    Um = models.CharField(max_length=100, null=True, blank=True, verbose_name='Um')
    Qtyord = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qtyord')
    Qtyship = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qtyship')
    Qtyback = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qtyback')
    Percost = models.CharField(max_length=100, null=True, blank=True, verbose_name='Percost')
    Fpercost = models.CharField(max_length=100, null=True, blank=True, verbose_name='Fpercost')
    Price = models.CharField(max_length=100, null=True, blank=True, verbose_name='Price')
    Fprice = models.CharField(max_length=100, null=True, blank=True, verbose_name='Fprice')
    Discamt = models.CharField(max_length=100, null=True, blank=True, verbose_name='Discamt')
    Fdiscamt = models.CharField(max_length=100, null=True, blank=True, verbose_name='Fdiscamt')
    Extension = models.CharField(max_length=100, null=True, blank=True, verbose_name='Extension')
    Fextension = models.CharField(max_length=100, null=True, blank=True, verbose_name='Fextension')
    Weight = models.CharField(max_length=100, null=True, blank=True, verbose_name='Weight')
    Factor = models.CharField(max_length=100, null=True, blank=True, verbose_name='Factor')
    Explode = models.CharField(max_length=100, null=True, blank=True, verbose_name='Explode')
    Aftersub = models.CharField(max_length=100, null=True, blank=True, verbose_name='Aftersub')
    Buildkit = models.CharField(max_length=100, null=True, blank=True, verbose_name='Buildkit')
    Pricechg = models.CharField(max_length=100, null=True, blank=True, verbose_name='Pricechg')
    Isinvalid = models.CharField(max_length=100, null=True, blank=True, verbose_name='Isinvalid')
    Isspeprice = models.CharField(max_length=100, null=True, blank=True, verbose_name='Isspeprice')
    Press = models.CharField(max_length=100, null=True, blank=True, verbose_name='Press')
    Pss1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Pss1')
    Pss2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Pss2')
    Setupt1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Setupt1')
    Setupt2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Setupt2')
    Stock = models.CharField(max_length=100, null=True, blank=True, verbose_name='Stock')
    Size = models.CharField(max_length=100, null=True, blank=True, verbose_name='Size')
    Blackink = models.CharField(max_length=100, null=True, blank=True, verbose_name='Blackink')
    Pplates = models.CharField(max_length=100, null=True, blank=True, verbose_name='Pplates')
    Side12 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Side12')
    Numoflots = models.CharField(max_length=100, null=True, blank=True, verbose_name='Numoflots')
    Outs = models.CharField(max_length=100, null=True, blank=True, verbose_name='Outs')
    Units = models.CharField(max_length=100, null=True, blank=True, verbose_name='Units')
    Diflev1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Diflev1')
    Diflev2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Diflev2')
    Presstime = models.CharField(max_length=100, null=True, blank=True, verbose_name='Presstime')
    Act_time = models.CharField(max_length=100, null=True, blank=True, verbose_name='Act_time')
    Sheets = models.CharField(max_length=100, null=True, blank=True, verbose_name='Sheets')
    Impres = models.CharField(max_length=100, null=True, blank=True, verbose_name='Impres')
    Overmanual = models.CharField(max_length=100, null=True, blank=True, verbose_name='Overmanual')
    Overs = models.CharField(max_length=100, null=True, blank=True, verbose_name='Overs')
    Pass1s = models.CharField(max_length=100, null=True, blank=True, verbose_name='Pass1s')
    Pass2s = models.CharField(max_length=100, null=True, blank=True, verbose_name='Pass2s')
    Vp = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vp')
    Vpw = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vpw')
    Vpl = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vpl')
    Vfw = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vfw')
    Vfl = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vfl')
    Press_w = models.CharField(max_length=100, null=True, blank=True, verbose_name='Press_w')
    Press_l = models.CharField(max_length=100, null=True, blank=True, verbose_name='Press_l')
    Vppl = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vppl')
    Inkside1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Inkside1')
    Inkside2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Inkside2')
    Workturn = models.CharField(max_length=100, null=True, blank=True, verbose_name='Workturn')
    Setmargin = models.CharField(max_length=100, null=True, blank=True, verbose_name='Setmargin')
    Margin = models.CharField(max_length=100, null=True, blank=True, verbose_name='Margin')
    Transfered = models.CharField(max_length=100, null=True, blank=True, verbose_name='Transfered')
    Trimtype = models.CharField(max_length=100, null=True, blank=True, verbose_name='Trimtype')
    Schedule = models.CharField(max_length=100, null=True, blank=True, verbose_name='Schedule')
    Job_Category = models.CharField(max_length=100, null=True, blank=True, verbose_name='Job Category')
    Sizen = models.CharField(max_length=100, null=True, blank=True, verbose_name='Sizen')
    Jobtype = models.CharField(max_length=100, null=True, blank=True, verbose_name='Jobtype')
    Unitprice = models.CharField(max_length=100, null=True, blank=True, verbose_name='Unitprice')
    Depttime = models.CharField(max_length=100, null=True, blank=True, verbose_name='Depttime')
    Stockqty = models.CharField(max_length=100, null=True, blank=True, verbose_name='Stockqty')
    Stockprice = models.CharField(max_length=100, null=True, blank=True, verbose_name='Stockprice')
    Items = models.CharField(max_length=100, null=True, blank=True, verbose_name='Items')
    Cutype = models.CharField(max_length=100, null=True, blank=True, verbose_name='Cutype')
    Jobitem = models.CharField(max_length=100, null=True, blank=True, verbose_name='Jobitem')
    Deptstot = models.CharField(max_length=100, null=True, blank=True, verbose_name='Deptstot')
    Item_Description = models.CharField(max_length=100, null=True, blank=True, verbose_name='Item Description')
    Quotn = models.CharField(max_length=100, null=True, blank=True, verbose_name='Quotn')
    Vendponum = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vendponum')
    Vendmarkup = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vendmarkup')
    Vendcostpu = models.CharField(max_length=100, null=True, blank=True, verbose_name='Vendcostpu')
    Salepaper = models.CharField(max_length=100, null=True, blank=True, verbose_name='Salepaper')
    Salelabor = models.CharField(max_length=100, null=True, blank=True, verbose_name='Salelabor')
    Costpaper = models.CharField(max_length=100, null=True, blank=True, verbose_name='Costpaper')
    Costlabor = models.CharField(max_length=100, null=True, blank=True, verbose_name='Costlabor')
    Profpaper = models.CharField(max_length=100, null=True, blank=True, verbose_name='Profpaper')
    Proflabor = models.CharField(max_length=100, null=True, blank=True, verbose_name='Proflabor')
    Platesale = models.CharField(max_length=100, null=True, blank=True, verbose_name='Platesale')
    Platecost = models.CharField(max_length=100, null=True, blank=True, verbose_name='Platecost')
    Profplate = models.CharField(max_length=100, null=True, blank=True, verbose_name='Profplate')
    Matcost = models.CharField(max_length=100, null=True, blank=True, verbose_name='Matcost')
    Labcost = models.CharField(max_length=100, null=True, blank=True, verbose_name='Labcost')
    Emp = models.CharField(max_length=100, null=True, blank=True, verbose_name='Emp')
    Colordesc = models.CharField(max_length=100, null=True, blank=True, verbose_name='Colordesc')
    Done = models.CharField(max_length=100, null=True, blank=True, verbose_name='Done')
    Orditem = models.CharField(max_length=100, null=True, blank=True, verbose_name='Orditem')
    Grain = models.CharField(max_length=100, null=True, blank=True, verbose_name='Grain')
    Grain1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Grain1')
    Isparent = models.CharField(max_length=100, null=True, blank=True, verbose_name='Isparent')
    Cuts = models.CharField(max_length=100, null=True, blank=True, verbose_name='Cuts')
    Usecuts = models.CharField(max_length=100, null=True, blank=True, verbose_name='Usecuts')
    Qty1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qty1')
    Qty2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qty2')
    Qty3 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qty3')
    Qty4 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qty4')
    Qty5 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qty5')
    Qty6 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Qty6')
    Orddate = models.CharField(max_length=100, null=True, blank=True, verbose_name='Orddate')
    Mouts = models.CharField(max_length=100, null=True, blank=True, verbose_name='Mouts')
    Prttable = models.CharField(max_length=100, null=True, blank=True, verbose_name='Prttable')
    Accessed = models.CharField(max_length=100, null=True, blank=True, verbose_name='Accessed')
    Itemlink = models.CharField(max_length=100, null=True, blank=True, verbose_name='Itemlink')
    Pricem = models.CharField(max_length=100, null=True, blank=True, verbose_name='Pricem')
    Action = models.CharField(max_length=100, null=True, blank=True, verbose_name='Action')
    Overcopy = models.CharField(max_length=100, null=True, blank=True, verbose_name='Overcopy')
    Project = models.CharField(max_length=100, null=True, blank=True, verbose_name='Project')
    Plevel = models.CharField(max_length=100, null=True, blank=True, verbose_name='Plevel')
    Numofons = models.CharField(max_length=100, null=True, blank=True, verbose_name='Numofons')
    Useons = models.CharField(max_length=100, null=True, blank=True, verbose_name='Useons')
    Plate12 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Plate12')
    Passink1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Passink1')
    Passink2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Passink2')
    Forecast = models.CharField(max_length=100, null=True, blank=True, verbose_name='Forecast')
    Foreperc = models.CharField(max_length=100, null=True, blank=True, verbose_name='Foreperc')
    Shpqty = models.CharField(max_length=100, null=True, blank=True, verbose_name='Shpqty')
    Shpprt = models.CharField(max_length=100, null=True, blank=True, verbose_name='Shpprt')
    Orgstat = models.CharField(max_length=100, null=True, blank=True, verbose_name='Orgstat')
    Worktumb = models.CharField(max_length=100, null=True, blank=True, verbose_name='Worktumb')
    Waste1 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Waste1')
    Waste2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Waste2')
    Sortdone = models.CharField(max_length=100, null=True, blank=True, verbose_name='Sortdone')
    Oldstock = models.CharField(max_length=100, null=True, blank=True, verbose_name='Oldstock')
    Press2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Press2')
    Overcop2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Overcop2')
    Unitpric2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Unitpric2')
    Stockpric2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Stockpric2')
    Attached = models.CharField(max_length=100, null=True, blank=True, verbose_name='Attached')
    Packprt = models.CharField(max_length=100, null=True, blank=True, verbose_name='Packprt')
    Premium = models.CharField(max_length=100, null=True, blank=True, verbose_name='Premium')
    Overperm = models.CharField(max_length=100, null=True, blank=True, verbose_name='Overperm')
    Overhour = models.CharField(max_length=100, null=True, blank=True, verbose_name='Overhour')
    Hourly = models.CharField(max_length=100, null=True, blank=True, verbose_name='Hourly')
    Spi = models.CharField(max_length=100, null=True, blank=True, verbose_name='Spi')
    Cpi = models.CharField(max_length=100, null=True, blank=True, verbose_name='Cpi')
    Gpd = models.CharField(max_length=100, null=True, blank=True, verbose_name='Gpd')
    Gpp = models.CharField(max_length=100, null=True, blank=True, verbose_name='Gpp')
    Gpest = models.CharField(max_length=100, null=True, blank=True, verbose_name='Gpest')
    Gpact = models.CharField(max_length=100, null=True, blank=True, verbose_name='Gpact')
    Gpside = models.CharField(max_length=100, null=True, blank=True, verbose_name='Gpside')
    Hourly2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Hourly2')
    Overhou2 = models.CharField(max_length=100, null=True, blank=True, verbose_name='Overhou2')

    def __str__(self):
        return self.OrderNum
    
class PrintleaderSORITL(models.Model):
    Invoice = models.CharField(max_length=100, null=True, blank=True, verbose_name='Invoice')
    Done = models.CharField(max_length=100, null=True, blank=True, verbose_name='Done')
    Item = models.CharField(max_length=100, null=True, blank=True, verbose_name='Item')
    E_deptn = models.CharField(max_length=100, null=True, blank=True, verbose_name='E_deptn')
    E_yn = models.CharField(max_length=100, null=True, blank=True, verbose_name='E_yn')
    E_field = models.CharField(max_length=100, null=True, blank=True, verbose_name='E_field')
    E_desc = models.CharField(max_length=100, null=True, blank=True, verbose_name='E_desc')
    E_um = models.CharField(max_length=100, null=True, blank=True, verbose_name='E_um')
    E_units = models.CharField(max_length=100, null=True, blank=True, verbose_name='E_units')
    E_amt = models.CharField(max_length=100, null=True, blank=True, verbose_name='E_amt')
    E_setup = models.CharField(max_length=100, null=True, blank=True, verbose_name='E_setup')
    Unitshr = models.CharField(max_length=100, null=True, blank=True, verbose_name='Unitshr')
    Stime = models.CharField(max_length=100, null=True, blank=True, verbose_name='Stime')
    Ptime = models.CharField(max_length=100, null=True, blank=True, verbose_name='Ptime')
    Dact_time = models.CharField(max_length=100, null=True, blank=True, verbose_name='Dact_time')
    Itemtotal = models.CharField(max_length=100, null=True, blank=True, verbose_name='Itemtotal')
    Unitcost = models.CharField(max_length=100, null=True, blank=True, verbose_name='Unitcost')
    Workmess = models.CharField(max_length=200, null=True, blank=True, verbose_name='Workmess')
    Barcode = models.CharField(max_length=100, null=True, blank=True, verbose_name='Barcode')
    Taxitem = models.CharField(max_length=100, null=True, blank=True, verbose_name='Taxitem')
    Taxperc = models.CharField(max_length=100, null=True, blank=True, verbose_name='Taxperc')
    Bhc = models.CharField(max_length=100, null=True, blank=True, verbose_name='Bhc')
    Costcent = models.CharField(max_length=100, null=True, blank=True, verbose_name='Costcent')
    Emp = models.CharField(max_length=100, null=True, blank=True, verbose_name='Emp')
    Schedule = models.CharField(max_length=100, null=True, blank=True, verbose_name='Schedule')
    Prodhrs = models.CharField(max_length=100, null=True, blank=True, verbose_name='Prodhrs')
    Ordersort = models.CharField(max_length=100, null=True, blank=True, verbose_name='Ordersort')
    Orditem = models.CharField(max_length=100, null=True, blank=True, verbose_name='Orditem')
    Type = models.CharField(max_length=100, null=True, blank=True, verbose_name='Type')
    Accessed = models.CharField(max_length=100, null=True, blank=True, verbose_name='Accessed')
    Action = models.CharField(max_length=100, null=True, blank=True, verbose_name='Action')
    Keyid = models.CharField(max_length=100, null=True, blank=True, verbose_name='Keyid')
    Sortdone = models.CharField(max_length=100, null=True, blank=True, verbose_name='Sortdone')

    def __str__(self):
        return self.Invoice
    
