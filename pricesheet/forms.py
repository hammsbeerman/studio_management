from django import forms
from django.forms import ModelForm
from django.urls import reverse_lazy
from .models import PriceSheet
from controls.models import SubCategory, Category
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class EnvelopeForm(forms.ModelForm):

    class Meta:
        model = PriceSheet
        fields = [
            'description', 'set_per_book', 'pages_per_book', 'qty_of_sheets', 'original_size', 'press_sheet_per_parent',
            'gangup', 'overage', 'output_per_sheet', 'parent_sheets_required', 'side_1_clicks', 'side_2_clicks', 'side_1_inktype', 'side_2_inktype', 'paper_stock', 'price_per_m', 
            'step_workorder_price', 'step_reclaim_artwork_price', 'step_send_to_press_price', 'material_cost', 'material_markup_percentage', 'material_markup', 'step_print_cost_side_1', 
            'step_print_cost_side_1_price', 'step_print_cost_side_2', 'step_print_cost_side_2_price', 'step_count_package_price', 'step_delivery_price', 'step_packing_slip_price', 'price_total', 'price_total_per_m', 'misc1_description', 'misc1_price', 'misc2_description', 'misc2_price', 'misc3_description',
            'misc3_price', 'misc4_description', 'misc4_price'
        ]
        labels = {
            'set_per_book':'Qty',

        }

class SubCategoryForm(forms.ModelForm):

    class Meta:
        model = SubCategory
        fields = ['category', 'name', 'description']

class CategoryForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = ['name', 'description', 'design_type', 'formname', 'modal']

class CreateTemplateForm(forms.ModelForm):

    class Meta:
        model = PriceSheet
        fields = ['category', 'subcategory', 'name', 'description']

class NCRForm(forms.ModelForm):

    class Meta:
        model = PriceSheet
        fields = [
            'description', 'set_per_book', 'pages_per_book', 'qty_of_sheets', 'original_size', 'press_size', 'press_sheet_per_parent',
            'flat_size', 'finished_size', 'gangup', 'overage', 'output_per_sheet', 'parent_sheets_required', 'side_1_clicks', 'side_2_clicks', 'side_1_inktype', 'side_2_inktype', 'paper_stock', 'price_per_m', 
            'step_workorder_price', 'step_reclaim_artwork_price', 'step_send_to_press_price', 'material_cost', 'material_markup_percentage', 'material_markup', 'step_print_cost_side_1', 
            'step_print_cost_side_1_price', 'step_print_cost_side_2', 'step_id_count_price', 'step_print_cost_side_2_price', 'step_count_package_price', 'step_delivery_price', 'step_packing_slip_price', 'price_total', 'price_total_per_m', 'misc1_description', 'misc1_price', 'misc2_description', 'misc2_price', 'misc3_description',
            'misc3_price', 'misc4_description', 'misc4_price'
        ]
        labels = {
            'set_per_book':'Qty',
            'pages_per_book':'How many parts'
        }

class NewTemplateForm(forms.ModelForm):

    class Meta:
        model = PriceSheet
        fields = [
            'description', 'set_per_book', 'pages_per_book', 'qty_of_sheets', 'original_size', 'press_size', 'press_sheet_per_parent',
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
            'misc3_price', 'misc4_description', 'misc4_price'
        ]
        widgets = {
            'set_per_book': forms.NumberInput(attrs={}),
            'pages_per_book': forms.NumberInput(attrs={}),
            'press_sheet_per_parent': forms.NumberInput(attrs={}),
            'output_per_sheet': forms.TextInput(attrs={'readonly':'readonly'}),
            'qty_of_sheets': forms.TextInput(attrs={'readonly':'readonly'}),
            'parent_sheets_required': forms.TextInput(attrs={'readonly':'readonly'}),
            #'paper_stock': forms.Select(attrs={'hx-name':'paper', 'hx-get':"{% url 'krueger:paper' %}", 'hx-trigger':'change', 'hx-target':'#id_price_per_m'}),
            'side_1_clicks': forms.TextInput(attrs={'readonly':'readonly'}),
            'side_2_clicks': forms.TextInput(attrs={'readonly':'readonly'}),
            'step_print_cost_side_1': forms.TextInput(attrs={'title': 'BW: .1, Color .15'}),
            'step_print_cost_side_2': forms.TextInput(attrs={'title': 'BW: .1, Color .15'}),
            'step_print_cost_side_1_price': forms.TextInput(attrs={'readonly':'readonly'}),
            'step_print_cost_side_2_price': forms.TextInput(attrs={'readonly':'readonly'}),
            'step_print_mailmerge_price': forms.TextInput(attrs={'readonly':'readonly'}),
            'step_perf_price': forms.TextInput(attrs={'readonly':'readonly'}),
            'step_number_price': forms.TextInput(attrs={'readonly':'readonly'}),
            #'step_perf_price': forms.TextInput(attrs={'readonly':'readonly'}),
            'step_staple_price': forms.TextInput(attrs={'readonly':'readonly'}),
            'step_fold_price': forms.TextInput(attrs={'readonly':'readonly'}),
            'step_perf_price': forms.TextInput(attrs={'readonly':'readonly'}),

        }

    """def clean_jobnumber(self):
        jobnumber = self.cleaned_data.get('jobnumber')
        if not jobnumber:
            raise forms.ValidationError('This field is required')
        return jobnumber"""


    """def clean_customer(self):
        customer = self.cleaned_data.get('customer')
        if not customer:
            raise forms.ValidationError('This field is required')
        return customer"""
    
    """ Uncomment these to force form validation
    def clean_company(self):
        company = self.cleaned_data.get('company')
        if not company:
            raise forms.ValidationError('This field is required')
        return company
        """
    
    """def clean_description(self):
        paper_stock = self.cleaned_data.get('paper_stock')
        if not paper_stock:
            raise forms.ValidationError('This field is required')
        return paper_stock"""
    
    """def clean_qty(self):
        qty = self.cleaned_data.get('qty')
        if not qty:
            raise forms.ValidationError('This field is required')
        return qty"""
################### NEW TEMPLATE FORM ENDS HERE #####################################