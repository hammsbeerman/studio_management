# Generated by Django 4.2.9 on 2024-02-12 17:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('inventory', '0001_initial'),
        ('controls', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceSheet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('description', models.CharField(blank=True, max_length=100, null=True, verbose_name='Description')),
                ('set_per_book', models.PositiveIntegerField(blank=True, null=True, verbose_name='# of sets / books/ pieces')),
                ('pages_per_book', models.PositiveBigIntegerField(blank=True, null=True, verbose_name='Pages per Book')),
                ('qty_of_sheets', models.CharField(blank=True, max_length=10, null=True, verbose_name='Qty of Sheets')),
                ('original_size', models.CharField(blank=True, max_length=100, null=True, verbose_name='Original Size')),
                ('press_size', models.CharField(blank=True, max_length=100, null=True, verbose_name='Press Size')),
                ('press_sheet_per_parent', models.PositiveBigIntegerField(blank=True, null=True, verbose_name='Press sheets / Parent')),
                ('flat_size', models.CharField(blank=True, max_length=100, null=True, verbose_name='Flat Size')),
                ('finished_size', models.CharField(blank=True, max_length=100, null=True, verbose_name='Finished Size')),
                ('gangup', models.PositiveBigIntegerField(blank=True, null=True, verbose_name='Gangup')),
                ('overage', models.PositiveBigIntegerField(blank=True, null=True, verbose_name='Overage')),
                ('output_per_sheet', models.CharField(blank=True, max_length=10, null=True, verbose_name='Output per Parent Sheet')),
                ('parent_sheets_required', models.CharField(blank=True, max_length=10, null=True, verbose_name='Parent Sheets Required')),
                ('side_1_clicks', models.CharField(blank=True, max_length=100, null=True, verbose_name='Side 1 Clicks')),
                ('side_2_clicks', models.CharField(blank=True, max_length=100, null=True, verbose_name='Side 2 Clicks')),
                ('side_1_inktype', models.CharField(choices=[('B/W', 'B/W'), ('Color', 'Color'), ('None', 'None'), ('Vivid', 'Vivid'), ('Vivid Plus', 'Vivid Plus')], max_length=100, verbose_name='Side 1 Ink')),
                ('side_2_inktype', models.CharField(choices=[('B/W', 'B/W'), ('Color', 'Color'), ('None', 'None'), ('Vivid', 'Vivid'), ('Vivid Plus', 'Vivid Plus')], max_length=100, verbose_name='Side 1 Ink')),
                ('price_per_m', models.CharField(blank=True, max_length=100, null=True, verbose_name='Paper Stock Price per M')),
                ('step_workorder_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Create Workorder')),
                ('step_reclaim_artwork_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Reclaim Artwork')),
                ('step_send_to_press_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Send to Press')),
                ('step_send_mailmerge_to_press_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Send Mailmerge to press')),
                ('mailmerge_qty', models.CharField(blank=True, max_length=12, null=True, verbose_name='Mailmerge Qty')),
                ('mailmerge_price_per_piece', models.CharField(blank=True, max_length=12, null=True, verbose_name='Mailmerge Price/Piece')),
                ('step_print_mailmerge_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Mailmerge')),
                ('material_cost', models.CharField(blank=True, max_length=12, null=True, verbose_name='Material Cost')),
                ('material_markup_percentage', models.CharField(blank=True, max_length=12, null=True, verbose_name='Material Markup Percent')),
                ('material_markup', models.CharField(blank=True, max_length=12, null=True, verbose_name='Material Markup Amount')),
                ('step_wear_and_tear_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Wear and Tear')),
                ('step_print_cost_side_1', models.CharField(blank=True, max_length=12, null=True, verbose_name='Side 1 Price / Click')),
                ('step_print_cost_side_1_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Print Cost Side 1')),
                ('step_print_cost_side_2', models.CharField(blank=True, max_length=12, null=True, verbose_name='Side 2 Price / Click')),
                ('step_print_cost_side_2_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Printing Cost Side 1')),
                ('step_trim_to_size_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Trim to Size')),
                ('step_NCR_compound_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='NCR Compound')),
                ('step_white_compound_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='White Compound')),
                ('step_set_to_perf_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Set to Perf')),
                ('perf_price_per_piece', models.CharField(blank=True, max_length=12, null=True, verbose_name='Price per Piece to Perf')),
                ('perf_number_of_pieces', models.CharField(blank=True, max_length=12, null=True, verbose_name='Pieces to Perf')),
                ('step_perf_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Cost to Perf')),
                ('step_set_to_number_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Set to Number')),
                ('number_price_to_number', models.CharField(blank=True, max_length=12, null=True, verbose_name='Price / Piece to Number')),
                ('number_number_of_pieces', models.CharField(blank=True, max_length=12, null=True, verbose_name='Pieces to Number')),
                ('step_number_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Cost to Number')),
                ('step_insert_frontback_cover_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Insert Front / Back Cover')),
                ('step_set_to_drill_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Set to Drill')),
                ('step_drill_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Drill')),
                ('step_set_to_staple_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Set to Staple')),
                ('staple_price_per_staple', models.CharField(blank=True, max_length=12, null=True, verbose_name='Price per staple')),
                ('staple_staples_per_piece', models.CharField(blank=True, max_length=12, null=True, verbose_name='Staples per piece')),
                ('staple_number_of_pieces', models.CharField(blank=True, max_length=12, null=True, verbose_name='Number of pieces')),
                ('step_staple_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Cost to Staple')),
                ('step_insert_wrap_around_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Insert Wrap Around')),
                ('step_insert_chip_divider_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Insert Chip Divider')),
                ('step_set_folder_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Set Folder')),
                ('fold_price_per_fold', models.CharField(blank=True, max_length=12, null=True, verbose_name='Price / Fold')),
                ('fold_number_to_fold', models.CharField(blank=True, max_length=12, null=True, verbose_name='Pieces to Fold')),
                ('step_fold_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Cost to Fold')),
                ('tabs_price_per_tab', models.CharField(blank=True, max_length=12, null=True, verbose_name='Price / Tab')),
                ('tabs_per_piece', models.CharField(blank=True, max_length=12, null=True, verbose_name='Tabs / Piece')),
                ('tabs_number_of_pieces', models.CharField(blank=True, max_length=12, null=True, verbose_name='Number of Pieces')),
                ('step_tab_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Cost to Tab for Mailing')),
                ('misc1_description', models.CharField(blank=True, max_length=50, null=True, verbose_name='Misc extra 1 description')),
                ('misc1_price', models.CharField(blank=True, max_length=50, null=True, verbose_name='Misc extra 1 price')),
                ('misc2_description', models.CharField(blank=True, max_length=50, null=True, verbose_name='Misc extra 2 description')),
                ('misc2_price', models.CharField(blank=True, max_length=50, null=True, verbose_name='Misc extra 2 price')),
                ('misc3_description', models.CharField(blank=True, max_length=50, null=True, verbose_name='Misc extra 3 description')),
                ('misc3_price', models.CharField(blank=True, max_length=50, null=True, verbose_name='Misc extra 3 price')),
                ('misc4_description', models.CharField(blank=True, max_length=50, null=True, verbose_name='Misc extra 4 description')),
                ('misc4_price', models.CharField(blank=True, max_length=50, null=True, verbose_name='Misc extra 4 price')),
                ('step_bulk_mail_tray_sort_paperwork_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Prepare Bulk Mailing')),
                ('step_id_count_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='ID / Count')),
                ('step_count_package_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Count / Package')),
                ('step_delivery_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Delivery')),
                ('step_packing_slip_price', models.CharField(blank=True, max_length=12, null=True, verbose_name='Packing Slip')),
                ('price_total', models.CharField(blank=True, max_length=10, null=True, verbose_name='Total Price')),
                ('price_total_per_m', models.CharField(blank=True, max_length=10, null=True, verbose_name='Price / M')),
                ('dateentered', models.DateTimeField(auto_now_add=True)),
                ('edited', models.BooleanField(default=False, verbose_name='Edited')),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='controls.category')),
                ('paper_stock', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='inventory.inventory')),
                ('subcategory', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='controls.subcategory')),
            ],
        ),
    ]
