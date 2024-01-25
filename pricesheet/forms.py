from django import forms
from django.forms import ModelForm
from django.urls import reverse_lazy
from .models import PriceSheet
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class EnvelopeForm(forms.ModelForm):

    class Meta:
        model = PriceSheet
        fields = [
            'description', 'set_per_book', 'pages_per_book', 'qty_of_sheets', 'original_size', 'press_size', 'press_size_per_parent',
            'flat_size', 'finished_size', 'gangup', 'overage', 'output_per_sheet', 'parent_sheets_required', 'side_1_clicks', 'side_2_clicks', 'paper_stock', 'price_per_m', 
            'step_workorder_price', 'step_reclaim_artwork_price', 'step_send_to_press_price', 'material_cost', 'material_markup_percentage', 'material_markup', 'step_print_cost_side_1', 
            'step_print_cost_side_1_price', 'step_print_cost_side_2', 'step_print_cost_side_2_price', 'step_count_package_price', 'step_delivery_price', 'step_packing_slip_price', 'price_total', 'price_total_per_m', 'misc1_description', 'misc1_price', 'misc2_description', 'misc2_price', 'misc3_description',
            'misc3_price', 'misc4_description', 'misc4_price'
        ]