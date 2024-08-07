# Generated by Django 4.2.9 on 2024-07-25 17:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('printleader', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrintleaderARINVODA',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('InvoiceNum', models.CharField(blank=True, max_length=200, null=True, verbose_name='InvoiceNum')),
                ('Lineno', models.CharField(blank=True, max_length=200, null=True, verbose_name='Lineno')),
                ('Linetype', models.CharField(blank=True, max_length=200, null=True, verbose_name='Linetype')),
                ('Chgcode', models.CharField(blank=True, max_length=200, null=True, verbose_name='Chgcode')),
                ('Descript', models.CharField(blank=True, max_length=200, null=True, verbose_name='Descript')),
                ('Acctnum', models.CharField(blank=True, max_length=200, null=True, verbose_name='Acctnum')),
                ('Qty', models.CharField(blank=True, max_length=200, null=True, verbose_name='Qty')),
                ('Percost', models.CharField(blank=True, max_length=200, null=True, verbose_name='Percost')),
                ('Fpercost', models.CharField(blank=True, max_length=200, null=True, verbose_name='Fpercost')),
                ('Price', models.CharField(blank=True, max_length=200, null=True, verbose_name='Price')),
                ('Fprice', models.CharField(blank=True, max_length=200, null=True, verbose_name='Fprice')),
                ('Taxable', models.CharField(blank=True, max_length=200, null=True, verbose_name='Taxable')),
                ('Commable', models.CharField(blank=True, max_length=200, null=True, verbose_name='Commable')),
                ('Extension', models.CharField(blank=True, max_length=200, null=True, verbose_name='Extension')),
                ('Fextension', models.CharField(blank=True, max_length=200, null=True, verbose_name='Fextension')),
                ('Items', models.CharField(blank=True, max_length=200, null=True, verbose_name='Items')),
                ('Job_Category', models.CharField(blank=True, max_length=200, null=True, verbose_name='Job Category')),
                ('Jobname', models.CharField(blank=True, max_length=200, null=True, verbose_name='Jobname')),
                ('Jnlbatch', models.CharField(blank=True, max_length=200, null=True, verbose_name='Jnlbatch')),
                ('Itemnum', models.CharField(blank=True, max_length=200, null=True, verbose_name='Itemnum')),
                ('Discount', models.CharField(blank=True, max_length=200, null=True, verbose_name='Discount')),
                ('Discperc', models.CharField(blank=True, max_length=200, null=True, verbose_name='Discperc')),
                ('Press', models.CharField(blank=True, max_length=200, null=True, verbose_name='Press')),
                ('Pss1', models.CharField(blank=True, max_length=200, null=True, verbose_name='Pss1')),
                ('Pss2', models.CharField(blank=True, max_length=200, null=True, verbose_name='Pss2')),
                ('Setupt1', models.CharField(blank=True, max_length=200, null=True, verbose_name='Setupt1')),
                ('Setupt2', models.CharField(blank=True, max_length=200, null=True, verbose_name='Setupt2')),
                ('Stock', models.CharField(blank=True, max_length=200, null=True, verbose_name='Stock')),
                ('Size', models.CharField(blank=True, max_length=200, null=True, verbose_name='Size')),
                ('Blackink', models.CharField(blank=True, max_length=200, null=True, verbose_name='Blackink')),
                ('Pplates', models.CharField(blank=True, max_length=200, null=True, verbose_name='Pplates')),
                ('Side12', models.CharField(blank=True, max_length=200, null=True, verbose_name='Side12')),
                ('Numoflots', models.CharField(blank=True, max_length=200, null=True, verbose_name='Numoflots')),
                ('Outs', models.CharField(blank=True, max_length=200, null=True, verbose_name='Outs')),
                ('Units', models.CharField(blank=True, max_length=200, null=True, verbose_name='Units')),
                ('Diflev1', models.CharField(blank=True, max_length=200, null=True, verbose_name='Diflev1')),
                ('Diflev2', models.CharField(blank=True, max_length=200, null=True, verbose_name='Diflev2')),
                ('Presstime', models.CharField(blank=True, max_length=200, null=True, verbose_name='Presstime')),
                ('Act_time', models.CharField(blank=True, max_length=200, null=True, verbose_name='Act_time')),
                ('Sheets', models.CharField(blank=True, max_length=200, null=True, verbose_name='Sheets')),
                ('Impres', models.CharField(blank=True, max_length=200, null=True, verbose_name='Impres')),
                ('Overmanual', models.CharField(blank=True, max_length=200, null=True, verbose_name='Overmanual')),
                ('Overs', models.CharField(blank=True, max_length=200, null=True, verbose_name='Overs')),
                ('Pass1s', models.CharField(blank=True, max_length=200, null=True, verbose_name='Pass1s')),
                ('Pass2s', models.CharField(blank=True, max_length=200, null=True, verbose_name='Pass2s')),
                ('Vp', models.CharField(blank=True, max_length=200, null=True, verbose_name='Vp')),
                ('Vpw', models.CharField(blank=True, max_length=200, null=True, verbose_name='Vpw')),
                ('Vpl', models.CharField(blank=True, max_length=200, null=True, verbose_name='Vpl')),
                ('Vfw', models.CharField(blank=True, max_length=200, null=True, verbose_name='Vfw')),
                ('Vfl', models.CharField(blank=True, max_length=200, null=True, verbose_name='Vfl')),
                ('Press_w', models.CharField(blank=True, max_length=200, null=True, verbose_name='Press_w')),
                ('Press_l', models.CharField(blank=True, max_length=200, null=True, verbose_name='Press_l')),
                ('Vppl', models.CharField(blank=True, max_length=200, null=True, verbose_name='Vppl')),
                ('Inkside1', models.CharField(blank=True, max_length=200, null=True, verbose_name='Inkside1')),
                ('Inkside2', models.CharField(blank=True, max_length=200, null=True, verbose_name='Inkside2')),
                ('Workturn', models.CharField(blank=True, max_length=200, null=True, verbose_name='Workturn')),
                ('Margin', models.CharField(blank=True, max_length=200, null=True, verbose_name='Margin')),
                ('Trimtype', models.CharField(blank=True, max_length=200, null=True, verbose_name='Trimtype')),
                ('Schedule', models.CharField(blank=True, max_length=200, null=True, verbose_name='Schedule')),
                ('Sizen', models.CharField(blank=True, max_length=200, null=True, verbose_name='Sizen')),
                ('Jobtype', models.CharField(blank=True, max_length=200, null=True, verbose_name='Jobtype')),
                ('Unitprice', models.CharField(blank=True, max_length=200, null=True, verbose_name='Unitprice')),
                ('Depttime', models.CharField(blank=True, max_length=200, null=True, verbose_name='Depttime')),
                ('Stockqty', models.CharField(blank=True, max_length=200, null=True, verbose_name='Stockqty')),
                ('Stockprice', models.CharField(blank=True, max_length=200, null=True, verbose_name='Stockprice')),
                ('Cutype', models.CharField(blank=True, max_length=200, null=True, verbose_name='Cutype')),
                ('Jobitem', models.CharField(blank=True, max_length=200, null=True, verbose_name='Jobitem')),
                ('Deptstot', models.CharField(blank=True, max_length=200, null=True, verbose_name='Deptstot')),
                ('Item_Description', models.CharField(blank=True, max_length=200, null=True, verbose_name='Item Description')),
                ('Vendponum', models.CharField(blank=True, max_length=200, null=True, verbose_name='Vendponum')),
                ('Vendmarkup', models.CharField(blank=True, max_length=200, null=True, verbose_name='Vendmarkup')),
                ('Vendcostpu', models.CharField(blank=True, max_length=200, null=True, verbose_name='Vendcostpu')),
                ('Salepaper', models.CharField(blank=True, max_length=200, null=True, verbose_name='Salepaper')),
                ('Salelabor', models.CharField(blank=True, max_length=200, null=True, verbose_name='Salelabor')),
                ('Costpaper', models.CharField(blank=True, max_length=200, null=True, verbose_name='Costpaper')),
                ('Costlabor', models.CharField(blank=True, max_length=200, null=True, verbose_name='Costlabor')),
                ('Profpaper', models.CharField(blank=True, max_length=200, null=True, verbose_name='Profpaper')),
                ('Proflabor', models.CharField(blank=True, max_length=200, null=True, verbose_name='Proflabor')),
                ('Platesale', models.CharField(blank=True, max_length=200, null=True, verbose_name='Platesale')),
                ('Platecost', models.CharField(blank=True, max_length=200, null=True, verbose_name='Platecost')),
                ('Profplate', models.CharField(blank=True, max_length=200, null=True, verbose_name='Profplate')),
                ('Matcost', models.CharField(blank=True, max_length=200, null=True, verbose_name='Matcost')),
                ('Labcost', models.CharField(blank=True, max_length=200, null=True, verbose_name='Labcost')),
                ('Done', models.CharField(blank=True, max_length=200, null=True, verbose_name='Done')),
                ('Orditem', models.CharField(blank=True, max_length=200, null=True, verbose_name='Orditem')),
                ('Grain', models.CharField(blank=True, max_length=200, null=True, verbose_name='Grain')),
                ('Isparent', models.CharField(blank=True, max_length=200, null=True, verbose_name='Isparent')),
                ('Cuts', models.CharField(blank=True, max_length=200, null=True, verbose_name='Cuts')),
                ('Usecuts', models.CharField(blank=True, max_length=200, null=True, verbose_name='Usecuts')),
                ('Qty1', models.CharField(blank=True, max_length=200, null=True, verbose_name='Qty1')),
                ('Qty2', models.CharField(blank=True, max_length=200, null=True, verbose_name='Qty2')),
                ('Qty3', models.CharField(blank=True, max_length=200, null=True, verbose_name='Qty3')),
                ('Qty4', models.CharField(blank=True, max_length=200, null=True, verbose_name='Qty4')),
                ('Qty5', models.CharField(blank=True, max_length=200, null=True, verbose_name='Qty5')),
                ('Qty6', models.CharField(blank=True, max_length=200, null=True, verbose_name='Qty6')),
                ('Orddate', models.CharField(blank=True, max_length=200, null=True, verbose_name='Orddate')),
                ('Grain1', models.CharField(blank=True, max_length=200, null=True, verbose_name='Grain1')),
                ('Mouts', models.CharField(blank=True, max_length=200, null=True, verbose_name='Mouts')),
                ('Prttable', models.CharField(blank=True, max_length=200, null=True, verbose_name='Prttable')),
                ('Itemlink', models.CharField(blank=True, max_length=200, null=True, verbose_name='Itemlink')),
                ('Pricem', models.CharField(blank=True, max_length=200, null=True, verbose_name='Pricem')),
                ('Action', models.CharField(blank=True, max_length=200, null=True, verbose_name='Action')),
                ('Overcopy', models.CharField(blank=True, max_length=200, null=True, verbose_name='Overcopy')),
                ('Project', models.CharField(blank=True, max_length=200, null=True, verbose_name='Project')),
                ('Plevel', models.CharField(blank=True, max_length=200, null=True, verbose_name='Plevel')),
                ('Numofons', models.CharField(blank=True, max_length=200, null=True, verbose_name='Numofons')),
                ('Useons', models.CharField(blank=True, max_length=200, null=True, verbose_name='Useons')),
                ('Plate12', models.CharField(blank=True, max_length=200, null=True, verbose_name='Plate12')),
                ('Passink1', models.CharField(blank=True, max_length=200, null=True, verbose_name='Passink1')),
                ('Passink2', models.CharField(blank=True, max_length=200, null=True, verbose_name='Passink2')),
                ('Forecast', models.CharField(blank=True, max_length=200, null=True, verbose_name='Forecast')),
                ('Foreperc', models.CharField(blank=True, max_length=200, null=True, verbose_name='Foreperc')),
                ('Shpqty', models.CharField(blank=True, max_length=200, null=True, verbose_name='Shpqty')),
                ('Shpprt', models.CharField(blank=True, max_length=200, null=True, verbose_name='Shpprt')),
                ('Orgstat', models.CharField(blank=True, max_length=200, null=True, verbose_name='Orgstat')),
                ('Worktumb', models.CharField(blank=True, max_length=200, null=True, verbose_name='Worktumb')),
                ('Waste1', models.CharField(blank=True, max_length=200, null=True, verbose_name='Waste1')),
                ('Waste2', models.CharField(blank=True, max_length=200, null=True, verbose_name='Waste2')),
                ('Press2', models.CharField(blank=True, max_length=200, null=True, verbose_name='Press2')),
                ('Overcop2', models.CharField(blank=True, max_length=200, null=True, verbose_name='Overcop2')),
                ('Unitpric2', models.CharField(blank=True, max_length=200, null=True, verbose_name='Unitpric2')),
                ('Attached', models.CharField(blank=True, max_length=200, null=True, verbose_name='Attached')),
                ('Packprt', models.CharField(blank=True, max_length=200, null=True, verbose_name='Packprt')),
                ('Premium', models.CharField(blank=True, max_length=200, null=True, verbose_name='Premium')),
                ('Overperm', models.CharField(blank=True, max_length=200, null=True, verbose_name='Overperm')),
                ('Overhour', models.CharField(blank=True, max_length=200, null=True, verbose_name='Overhour')),
                ('Hourly', models.CharField(blank=True, max_length=200, null=True, verbose_name='Hourly')),
                ('Hourly2', models.CharField(blank=True, max_length=200, null=True, verbose_name='Hourly2')),
            ],
        ),
    ]
