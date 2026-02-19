from django.contrib import admin
from django.urls import path
#from . import views

from .views import (
    bill_list,
    ar_dashboard,
    open_workorders,
    closed_workorders,
    recieve_payment,
    payment_detail,
    apply_payment,
    unapply_payment,
    unrecieve_payment,
    finance_main,
    #add_bill_payable,
    view_bills_payable,
    add_daily_sale,
    view_daily_sales,
    ar_aging,
    krueger_ar_aging,
    complete_not_billed,
    apply_other,
    krueger_ar,
    lk_ar,
    all_printleader,
    all_lk,
    open_invoices,
    open_invoices_recieve_payment,
    payment_history,
    remove_payment,
    all_open_printleader,
    invoice_detail,
    add_invoice_item,
    edit_invoice_item,
    delete_invoice_item,
    add_item_to_vendor,
    add_inventory_item,
    vendor_item_remainder,
    add_invoice,
    edit_invoice,
    bills_by_vendor,
    edit_invoice_modal,
    invoice_detail_highlevel,
    bulk_edit_invoices,
    payment_history_customer,
    sales_tax_payable,
    office_supplies_pos_tax,
    monthly_statements,
    sales_comparison_report,
    sales_comparison_debug,
    unapply_workorder_payment,
    unapplied_and_credits_customer,
    creditmemo_create,
    apply_creditmemo_modal,
    apply_creditmemo,
    unapply_creditmemo,
    convert_payment_to_creditmemo,
    giftcertificate_issue,
    apply_giftcert_modal,
    apply_giftcert,
    unapply_giftcert,
    ar_action_buttons,
    apply_unapplied_payment_modal,
    orphan_payments_report,
    recompute_payment_available,
    orphan_payment_void,
    orphan_payment_force_apply_modal,
    ar_void_payment,
    ar_void_credit_memo,
    ar_void_giftcert,
    ar_void_payment_modal,
    ar_void_creditmemo_modal,
    ar_void_giftcert_modal,
    apply_giftcert_by_number,
    apply_giftcert_by_number_modal,
    unused_giftcerts_apply_modal,
    customer_full_report,
    credits_report,
    credits_report_customer_modal,
    credits_report_customer_row,
    adjust_credit_modal,
    adjust_credit,

)

app_name='finance'

urlpatterns = [
    path("", finance_main, name="finance"),

    # Inventory / vendor helpers
    path("add_inventory_item/", add_inventory_item, name="add_inventory_item"),
    path("add_inventory_item/<int:vendor>/<int:invoice>/", add_inventory_item, name="add_inventory_item_vendor_invoice"),
    path("add_inventory_item/<int:baseitem>/", add_inventory_item, name="add_inventory_item_baseitem"),

    path("add_item_to_vendor/", add_item_to_vendor, name="add_item_to_vendor"),
    path("add_item_to_vendor/<int:vendor>/<int:invoice>/", add_item_to_vendor, name="add_item_to_vendor_vendor_invoice"),

    path("vendor_item_remainder/<int:vendor>/<int:invoice>/", vendor_item_remainder, name="vendor_item_remainder"),

    # AP
    path("ap/bill_list/", bill_list, name="ap_bill_list"),

    path("ap/add_invoice/", add_invoice, name="ap_add_invoice"),
    path("ap/add_invoice/<int:vendor>/", add_invoice, name="ap_add_invoice_vendor"),

    path("ap/edit_invoice/<int:invoice>/", edit_invoice, name="ap_edit_invoice"),
    path("ap/edit_invoice/<int:invoice>/<int:drop>/", edit_invoice, name="ap_edit_invoice_drop"),

    path("ap/edit_invoice_modal/<int:invoice>/", edit_invoice_modal, name="ap_edit_invoice_modal"),

    path("ap/bulk_edit_invoices/", bulk_edit_invoices, name="ap_bulk_edit_invoices"),
    path("ap/bulk_edit_invoices/<int:vendor>/", bulk_edit_invoices, name="ap_bulk_edit_invoices_vendor"),

    #path("ap/invoice_detail/", invoice_detail, name="ap_invoice_detail"),
    path("ap/invoice_detail/<int:id>/", invoice_detail, name="ap_invoice_detail_id"),
    path("ap/invoice_detail_highlevel/<int:id>/", invoice_detail_highlevel, name="ap_invoice_detail_highlevel"),

    path("ap/add_invoice_item/", add_invoice_item, name="ap_add_invoice_item"),
    path("ap/add_invoice_item/<int:invoice>/", add_invoice_item, name="ap_add_invoice_item_invoice"),
    path("ap/add_invoice_item/<int:invoice>/<int:vendor>/", add_invoice_item, name="ap_add_invoice_item_invoice_vendor"),
    path("ap/add_invoice_item/<int:invoice>/<int:vendor>/<int:type>", add_invoice_item, name="ap_add_invoice_item_invoice_vendor_type"),

    path("ap/edit_invoice_item/<int:id>/", edit_invoice_item, name="ap_edit_invoice_item"),
    path("ap/edit_invoice_item/<int:invoice>/<int:id>", edit_invoice_item, name="ap_edit_invoice_item_invoice"),

    path("ap/delete_invoice_item/<int:invoice>/<int:id>", delete_invoice_item, name="ap_delete_invoice_item"),

    # Bills / Sales
    path("view_bills/", view_bills_payable, name="view_bills_payable"),
    path("bills_by_vendor/", bills_by_vendor, name="bills_by_vendor"),
    path("daily_sale/", add_daily_sale, name="add_daily_sale"),
    path("view_sales/", view_daily_sales, name="view_daily_sales"),

    # AR + aging
    path("ar_aging/", ar_aging, name="ar_aging"),
    path("krueger_ar_aging/", krueger_ar_aging, name="krueger_ar_aging"),
    path("complete_not_billed/", complete_not_billed, name="complete_not_billed"),
    path("apply_other/<int:cust>/", apply_other, name="apply_other"),

    path("krueger_ar/", krueger_ar, name="krueger_ar"),
    path("lk_ar/", lk_ar, name="lk_ar"),
    path("all_printleader/", all_printleader, name="all_printleader"),
    path("all_open_printleader/", all_open_printleader, name="all_open_printleader"),
    path("all_lk/", all_lk, name="all_lk"),

    path("ar/unapply_workorder_payment/<int:wop_id>/", unapply_workorder_payment, name="unapply_workorder_payment"),

    # Open invoices (keep canonical as the simpler one)
    path("open_invoices/<int:pk>/", open_invoices, name="open_invoices"),
    path("open_invoices/<int:pk>/<int:msg>/", open_invoices, name="open_invoices_with_msg"),

    path("open_invoices_recieve_payment/<int:pk>/", open_invoices_recieve_payment, name="open_invoices_recieve_payment"),
    path("open_invoices_recieve_payment/<int:pk>/<int:msg>/", open_invoices_recieve_payment, name="open_invoices_recieve_payment_with_msg"),

    # Tax / reports
    path("sales_tax_payable/", sales_tax_payable, name="sales_tax_payable"),
    path("sales_tax_payable/<int:submit>/", sales_tax_payable, name="sales_tax_payable_submit"),

    path("office_supplies_pos_tax/", office_supplies_pos_tax, name="office_supplies_pos_tax"),
    path("monthly_statements/", monthly_statements, name="monthly_statements"),
    path("sales-comparison/", sales_comparison_report, name="sales_comparison_report"),
    path("sales-comparison/debug/", sales_comparison_debug, name="sales_comparison_debug"),

    path("ar/reports/orphan-payments/", orphan_payments_report, name="orphan_payments_report"),
    path("ar/reports/orphan-payments/<int:payment_id>/recompute/", recompute_payment_available, name="recompute_payment_available"),
    path("ar/reports/orphan-payments/<int:payment_id>/void/", orphan_payment_void, name="orphan_payment_void"),
    path("ar/reports/orphan-payments/<int:payment_id>/force-apply/", orphan_payment_force_apply_modal, name="orphan_payment_force_apply_modal"),
    path("ar/reports/customer-full/", customer_full_report, name="customer_full_report"),
    path("ar/reports/credits/", credits_report, name="credits_report"),
    path("ar/reports/credits/customer-modal/", credits_report_customer_modal, name="credits_report_customer_modal"),
    path("ar/reports/credits/customer-row/", credits_report_customer_row, name="credits_report_customer_row"),

    # AR dashboard + payments
    path("ar/dashboard/", ar_dashboard, name="ar_dashboard"),
    path("ar/dashboard/open_workorders/", open_workorders, name="open_workorders"),
    path("ar/dashboard/closed_workorders/<int:cust>/", closed_workorders, name="closed_workorders"),

    path("ar/recieve_payment/", recieve_payment, name="recieve_payment"),
    path("ar/unrecieve_payment/", unrecieve_payment, name="unrecieve_payment"),
    path("ar/recieve_payment/payment_detail/", payment_detail, name="payment_detail"),
    path("ar/recieve_payment/apply_payment/", apply_payment, name="apply_payment"),
    path("ar/recieve_payment/unapply_payment/", unapply_payment, name="unapply_payment"),
    path("ar/payments/<int:payment_id>/void/", ar_void_payment, name="ar_void_payment"),
    path("ar/credit-memos/<int:cm_id>/void/", ar_void_credit_memo, name="creditmemo_void"),
    path("ar/giftcerts/<int:gc_id>/void/", ar_void_giftcert, name="giftcert_void"),

    # Pick ONE canonical payment_history; make the other an alias name
    path("ar/payment_history/", payment_history, name="payment_history"),
    path("ar/payment_history_customer/", payment_history_customer, name="payment_history_customer"),
    path("ar/recieve_payment/payment_history/", payment_history, name="payment_history_from_receive"),

    path("ar/remove_payment/", remove_payment, name="remove_payment"),
    path("ar/remove_payment/<int:pk>/", remove_payment, name="remove_payment_pk"),

    # Unapplied / Credits panel
    path("ar/unapplied/", unapplied_and_credits_customer, name="unapplied_and_credits_customer"),

    # Reverse/unapply existing payment application
    path("ar/unapply-workorder-payment/<int:wop_id>/", unapply_workorder_payment, name="unapply_workorder_payment"),
    path("ar/apply_unapplied_payment/<int:payment_id>/", apply_unapplied_payment_modal, name="apply_unapplied_payment_modal"),

    # Credit memo create + apply/unapply
    path("ar/creditmemo/new/", creditmemo_create, name="creditmemo_create"),
    path("ar/creditmemo/apply-modal/", apply_creditmemo_modal, name="apply_creditmemo_modal"),
    path("ar/creditmemo/apply/", apply_creditmemo, name="apply_creditmemo"),
    path("ar/creditmemo/unapply/<int:wocm_id>/", unapply_creditmemo, name="unapply_creditmemo"),

    # Convert payment available -> credit memo
    path("ar/payment/<int:payment_id>/convert-to-creditmemo/", convert_payment_to_creditmemo, name="convert_payment_to_creditmemo"),

    # Gift cert issue + apply/unapply
    path("ar/giftcert/new/", giftcertificate_issue, name="giftcertificate_issue"),
    path("ar/giftcert/apply-modal/", apply_giftcert_modal, name="apply_giftcert_modal"),
    path("ar/giftcert/apply/", apply_giftcert, name="apply_giftcert"),
    path("ar/giftcert/unapply/<int:gcr_id>/", unapply_giftcert, name="unapply_giftcert"),
    path("ar/giftcert/apply-by-number-modal/", apply_giftcert_by_number_modal, name="apply_giftcert_by_number_modal"),
    path("ar/giftcert/apply-by-number/", apply_giftcert_by_number, name="apply_giftcert_by_number"),
    path("ar/giftcert/unused-apply-modal/", unused_giftcerts_apply_modal, name="unused_giftcerts_apply_modal"),

    path("ar/action_buttons/", ar_action_buttons, name="ar_action_buttons"),

    path("ar/void/payment/<int:payment_id>/", ar_void_payment_modal, name="ar_void_payment_modal"),
    path("ar/void/credit-memo/<int:cm_id>/", ar_void_creditmemo_modal, name="ar_void_creditmemo_modal"),
    path("ar/void/giftcert/<int:gc_id>/", ar_void_giftcert_modal, name="ar_void_giftcert_modal"),

    path("ar/credits/adjust-modal/", adjust_credit_modal, name="adjust_credit_modal"),
    path("ar/credits/adjust/", adjust_credit, name="adjust_credit"),
]

