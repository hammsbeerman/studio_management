from django.contrib import admin
from .models import PaperStock, KruegerJobDetail

class PaperStockAdmin(admin.ModelAdmin):
    list_display = ('description', 'manufacturer', 'brand', 'weight', 'size', 'price_per_m')

admin.site.register(PaperStock, PaperStockAdmin)

class KruegerJobDetailAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(KruegerJobDetailAdmin, self).get_form(request, obj, **kwargs)
        field = form.base_fields["jobnumber"]
        field.widget.can_add_related = False
        field.widget.can_change_related = False
        field.widget.can_delete_related = False
        field.widget.can_view_related = True
        return form
    list_display = ('workorder', 'internal_company', 'customer', 'description', 'set_per_book', 'pages_per_book', 'qty_of_sheets', 'original_size', 'press_size', 'press_size_per_parent',
            'flat_size', 'finished_size', 'gangup', 'overage', 'output_per_sheet', 'parent_sheets_required', 'side_1_clicks', 'side_2_clicks', 'paper_stock', 'price_per_m', 
            #'flat_size', 'finished_size', 'gangup', 'overage', 'output_per_sheet', 'parent_sheets_required', 'side_1_clicks', 'side_2_clicks', 
            'step_workorder_price', 'step_reclaim_artwork_price', 'step_send_to_press_price', 'step_send_mailmerge_to_press_price', 'mailmerge_qty', 'mailmerge_price_per_piece', 
            'step_print_mailmerge_price', 'material_cost', 'material_markup_percentage', 'material_markup', 'step_wear_and_tear_price', 'step_print_cost_side_1', 
            'step_print_cost_side_1_price', 'step_print_cost_side_2', 'step_print_cost_side_2_price', 'step_trim_to_size_price', 'step_NCR_compound_price', 'step_white_compound_price', 
            'step_set_to_perf_price', 'perf_price_per_piece', 'perf_number_of_pieces', 'step_perf_price', 'step_set_to_number_price', 'number_price_to_number', 'number_number_of_pieces', 'step_number_price', 
            'step_insert_frontback_cover_price', 'step_set_to_drill_price', 'step_drill_price', 'step_set_to_staple_price', 'staple_price_per_staple', 'staple_staples_per_piece', 'staple_number_of_pieces', 
            'step_staple_price', 'step_insert_wrap_around_price', 'step_insert_chip_divider_price', 'step_set_folder_price', 'fold_price_per_fold', 'fold_number_to_fold', 'step_fold_price', 
            'tabs_price_per_tab', 'tabs_per_piece', 'tabs_number_of_pieces', 'step_tab_price', 'step_bulk_mail_tray_sort_paperwork_price', 'step_id_count_price', 'step_count_package_price', 
            'step_delivery_price', 'step_packing_slip_price', 'price_total', 'price_total_per_m', 'misc1_description', 'misc1_price', 'misc2_description', 'misc2_price', 'misc3_description',
            'misc3_price', 'misc4_description', 'misc4_price')
    
admin.site.register(KruegerJobDetail,KruegerJobDetailAdmin)