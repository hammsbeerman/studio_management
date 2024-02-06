# Generated by Django 4.2.9 on 2024-02-06 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0026_fixedcost_category_pricesheet_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fixedcost',
            name='value',
        ),
        migrations.AddField(
            model_name='fixedcost',
            name='create_workorder',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Create Workordeer'),
        ),
        migrations.AddField(
            model_name='fixedcost',
            name='duplo_1',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Value'),
        ),
        migrations.AddField(
            model_name='fixedcost',
            name='duplo_2',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Value'),
        ),
        migrations.AddField(
            model_name='fixedcost',
            name='duplo_3',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Value'),
        ),
        migrations.AddField(
            model_name='fixedcost',
            name='ncr_compound',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Value'),
        ),
        migrations.AddField(
            model_name='fixedcost',
            name='pad_compound',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Padding Compound'),
        ),
        migrations.AddField(
            model_name='fixedcost',
            name='reclaim_artwork',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Reclaim Workorder'),
        ),
        migrations.AddField(
            model_name='fixedcost',
            name='send_mailmerge_to_press',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Value'),
        ),
        migrations.AddField(
            model_name='fixedcost',
            name='send_to_press',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Value'),
        ),
        migrations.AddField(
            model_name='fixedcost',
            name='trim_to_size',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Value'),
        ),
        migrations.AddField(
            model_name='fixedcost',
            name='wear_and_tear',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Value'),
        ),
    ]
