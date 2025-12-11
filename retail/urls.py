from django.contrib import admin
from django.urls import path
#from . import views
from .retail_invoices import (
    add_vendor,
    vendor_list,
    vendor_detail,
    invoice_list,
)

from .views_reports import (
    inventory_sales_report,
    cash_sales_report
)

from .views import (
    #retail_home,
    #subcat,
    #parent,
    #invoice_detail,
    #add_invoice,
    #add_invoice_item,
    #invoice_item_remainder,
    #add_item_to_vendor,
    #add_inventory_item,
    # vendor_item_remainder,
    retail_inventory_list,
    #edit_invoice_item,
    #delete_invoice_item,
    retail_new_sale,
    retail_sale_detail,
    inventory_search,
    delete_line,
    update_line_field,
    add_line_from_inventory,
    set_sale_customer,
    retail_sale_customer_ar,
    #sale_create_workorder,
    sale_save_workorder,
    sale_pay_workorder,
    update_sale_notes,
    sale_totals,
    sale_customer_block,
    sale_header_actions,
    sale_totals_actions,
    sale_payment_modal,
    sale_payment_submit,
    sale_refund_start,
    refund_lookup,
    pos_sale_list,
    sale_toggle_tax,
    sale_send_as_quote,
    sale_add_custom_line,
    sale_receipt,
    sale_update_line_price,
    sale_update_line_variation,
    inventory_item_modal,
    pos_qty_sold_report,
    pos_qty_sold_item_detail,
    inventory_variation_modal,
    sale_receipt_modal,
    sale_toggle_delivery,
    delivery_report,
    delivery_reorder,
    delivery_update_date,
    sale_update_delivery_date,
    delivery_mark_delivered,


)

app_name='retail'

urlpatterns = [
    # path("", home, name="home"),
    # path("", retail_home, name="retail_home"),

    path("add_vendor/", add_vendor, name="add_vendor"),
    # path("add_invoice/", add_invoice, name="add_invoice"),
    # path("add_invoice_item/", add_invoice_item, name="add_invoice_item"),
    # path("add_invoice_item/<int:invoice>/<int:vendor>", add_invoice_item, name="add_invoice_item"),
    # path("add_invoice_item/<int:invoice>/", add_invoice_item, name="add_invoice_item"),
    # path("edit_invoice_item/<int:invoice>/<int:id>", edit_invoice_item, name="edit_invoice_item"),
    # path("edit_invoice_item/<int:id>/", edit_invoice_item, name="edit_invoice_item"),
    # path("invoice_item_remainder/<int:vendor>/<int:invoice>", invoice_item_remainder, name="invoice_item_remainder"),

    path("inventory/", retail_inventory_list, name="inventory_list"),
    path("invoices/", invoice_list, name="invoice_list"),
    path("vendors/", vendor_list, name="vendor_list"),
    path("vendors/<int:id>/", vendor_detail, name="vendor_detail"),
    path("vendor_list/", vendor_list, name="vendor_list"),
    path("invoice_list/", invoice_list, name="invoice_list"),
    path("vendor_detail/<int:id>/", vendor_detail, name="vendor_detail"),
    # path("invoice_detail/", invoice_detail, name="invoice_detail"),
    # path("invoice_detail/<int:id>/", invoice_detail, name="invoice_detail"),
    # path("subcat/<int:cat>/", subcat, name="subcat"),
    # path("parent/<int:cat>/", parent, name="parent"),
    # path("add_item_to_vendor/<int:vendor>/<int:invoice>", add_item_to_vendor, name="add_item_to_vendor"),
    # path("add_item_to_vendor/", add_item_to_vendor, name="add_item_to_vendor"),
    # path("add_inventory_item/<int:vendor>/<int:invoice>", add_inventory_item, name="add_inventory_item"),
    # path("add_inventory_item/", add_inventory_item, name="add_inventory_item"),
    # path("vendor_item_remainder/<int:vendor>/<int:invoice>", vendor_item_remainder, name="vendor_item_remainder"),

    path("retail_inventory_list/", retail_inventory_list, name="retail_inventory_list"),

    path("sale/new/", retail_new_sale, name="new_sale"),
    path("sale/<int:pk>/", retail_sale_detail, name="sale_detail"),
    path("sale/<int:pk>/set-customer/", set_sale_customer, name="set_sale_customer"),
    path("sale/<int:pk>/customer-ar/", retail_sale_customer_ar, name="sale_customer_ar"),

    # HTMX: add / update / delete lines, inventory search
    path("sale/<int:pk>/add-line/<int:inventory_id>/", add_line_from_inventory, name="add_line_from_inventory"),
    path("line/<int:line_id>/update/", update_line_field, name="update_line_field"),
    path("line/<int:line_id>/delete/", delete_line, name="delete_line"),
    path("inventory-search/", inventory_search, name="inventory_search"),
    path("inventory/<int:pk>/modal/", inventory_item_modal, name="inventory_item_modal"),

    # Workorder integration
    path("sale/<int:pk>/save-workorder/", sale_save_workorder, name="sale_save_workorder"),
    path("sale/<int:pk>/pay-workorder/", sale_pay_workorder, name="sale_pay_workorder"),
    path("sale/<int:pk>/send-as-quote/", sale_send_as_quote, name="sale_send_as_quote"),
    path("sale/<int:pk>/receipt/", sale_receipt, name="sale_receipt"),
    path("sale/<int:pk>/receipt/", sale_receipt_modal, name="sale_receipt_modal"),
    path("sale/<int:sale_pk>/line/<int:line_pk>/update/", sale_update_line_price, name="sale_update_line_price"),
    path("sale/<int:sale_pk>/item/<int:inventory_pk>/variation/", inventory_variation_modal, name="inventory_variation_modal"),

    # Sale metadata / totals / header partials
    path("sale/<int:pk>/update-notes/", update_sale_notes, name="update_sale_notes"),
    path("sale/<int:pk>/totals/", sale_totals, name="sale_totals"),
    path("sale/<int:pk>/customer-block/", sale_customer_block, name="sale_customer_block"),
    path("sale/<int:pk>/header-actions/", sale_header_actions, name="sale_header_actions"),
    path("sale/<int:pk>/totals-actions/", sale_totals_actions, name="sale_totals_actions"),
    path("sale/<int:pk>/toggle-tax/", sale_toggle_tax, name="sale_toggle_tax"),
    path("sale/<int:pk>/add-custom-line/", sale_add_custom_line, name="sale_add_custom_line"),
    path("sale/<int:sale_pk>/line/<int:line_pk>/set-variation/", sale_update_line_variation, name="sale_update_line_variation"),

    # Payments
    path("sale/<int:pk>/payment-modal/", sale_payment_modal, name="sale_payment_modal"),
    path("sale/<int:pk>/payment-submit/", sale_payment_submit, name="sale_payment_submit"),
    path("sale/<int:pk>/receipt/", sale_receipt_modal, name="sale_receipt_modal"),

    # Refunds
    path("sale/<int:pk>/refund-start/", sale_refund_start, name="sale_refund_start"),
    path("refund/lookup/", refund_lookup, name="refund_lookup"),

    # POS sales report/list
    path("pos/sales/", pos_sale_list, name="pos_sale_list"),
    path("reports/inventory-sales/", inventory_sales_report, name="inventory_sales_report"),
    path("reports/cash-sales/", cash_sales_report, name="cash_sales_report"),
    path("reports/pos-qty-sold/", pos_qty_sold_report, name="pos_qty_sold_report"),
    path("reports/pos-qty-sold/item/<int:item_id>/", pos_qty_sold_item_detail, name="pos_qty_sold_item_detail"),

    #Delivery
    path("sale/<int:pk>/toggle-delivery/", sale_toggle_delivery, name="sale_toggle_delivery"),
    path("sale/<int:pk>/delivery/date/", sale_update_delivery_date, name="sale_update_delivery_date"),
    path("delivery-report/", delivery_report, name="delivery_report"),
    path("delivery-report/reorder/", delivery_reorder, name="delivery_reorder"),
    path("delivery-report/update-date/", delivery_update_date, name="delivery_update_date"),
    path("delivery-report/mark-delivered/", delivery_mark_delivered, name="delivery_mark_delivered"),
]