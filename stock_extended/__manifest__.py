# -*- coding: utf-8 -*-
{
    "name": "Stock Extended",
    "summary": """
        Extend function of inventory module
    """,
    "description": """

    """,
    "author": "Odoo Freelancer",
    "website": "",
    "category": "Inventory",
    "version": "14.0.1.0.0",
    "depends": [
        "base",
        "stock",
        "stock_account",
        "base_extended",
        "purchase",
        "sale",
        "sale_stock",
        "point_of_sale",
        "asb_base_farmaku",
        "product_expiry",
        "product_extended",
        "asb_rest_api",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "data/ir_config_parameter.xml",
        "data/res_groups.xml",
        "data/ir_sequence.xml",
        "views/stock_quant_views.xml",
        "views/stock_warehouse_orderpoint_views.xml",
        "views/stock_move_line_views.xml",
        "views/purchase_order_views.xml",
        "views/stock_move_views.xml",
        "views/stock_move_line_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_valuation_layer_views.xml",
        "views/stock_picking_box_views.xml",
        "wizard/stock_report_wizard_views.xml",
        "wizard/stock_movement_report_wizard_views.xml",
        "wizard/orderpoint_report_wizard_views.xml",
        "wizard/stock_backorder_confirmation_views.xml",
        "report/orderpoint_report.xml",
        "report/report_deliveryslip.xml",
        "report/report_packing_list.xml",
        "report/new_report_deliveryslip.xml",
        "report/report_deliverylabel.xml",
        "report/stock_report_all_views.xml",
    ],
    "demo": [

    ],
}
