# Generated by Django 4.2.9 on 2024-02-06 22:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0027_remove_fixedcost_value_fixedcost_create_workorder_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='fixedcost',
            name='material_markup',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Material Markup Percentage'),
        ),
        migrations.AlterField(
            model_name='fixedcost',
            name='duplo_1',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Duplo1'),
        ),
        migrations.AlterField(
            model_name='fixedcost',
            name='duplo_2',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Duplo2'),
        ),
        migrations.AlterField(
            model_name='fixedcost',
            name='duplo_3',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Duplo3'),
        ),
        migrations.AlterField(
            model_name='fixedcost',
            name='ncr_compound',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='NCR Compound'),
        ),
        migrations.AlterField(
            model_name='fixedcost',
            name='reclaim_artwork',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Reclaim Artwork'),
        ),
        migrations.AlterField(
            model_name='fixedcost',
            name='send_mailmerge_to_press',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Send Mailmerge to press'),
        ),
        migrations.AlterField(
            model_name='fixedcost',
            name='send_to_press',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Send to press'),
        ),
        migrations.AlterField(
            model_name='fixedcost',
            name='trim_to_size',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Trim to Size'),
        ),
        migrations.AlterField(
            model_name='fixedcost',
            name='wear_and_tear',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Wear and Tear'),
        ),
    ]