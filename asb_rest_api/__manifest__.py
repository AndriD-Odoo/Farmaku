{
    "name": "Odoo Rest API",
    "version": "14.0.1.0.0",
    "author": "Arkana",
    "category": "Backend",
    "website": "https://www.arkana.co.id/",
    "summary": "Restful Api Service",
    "description": """""",
    "external_dependencies": {
         "python": ["simplejson"],
    },
    "depends": [
        "base",
        "stock",
        "account_extended",
        "asb_base_farmaku",
        "sale_management",
        "report_xlsx",
        "point_of_sale",
        "sale_extended",
        "ms_rest_api",
    ],
    "data": [
        "data/ir_config_parameter.xml",
        "data/ir_cron.xml",
        "security/ir.model.access.csv",
        "views/stock_picking_views.xml",
        "views/res_partner_view.xml",
        "views/sale_view.xml",
        "views/cancel_reason_view.xml",
        "views/product_rule_view.xml",
        "views/stock_view.xml",
        "views/log_import_pharmacyproduct_view.xml",
        "views/res_company_view.xml",
        "views/connector_farmaku_view.xml",
        "views/sync_stock_log_views.xml",
        "views/account_move_views.xml",
        "wizards/sync_pharmacies_view.xml",
        "wizards/cancel_reason_wizard_view.xml",
        "wizards/import_failed_order_wizard_views.xml",
        "reports/report.xml",
        "reports/sale_report.xml",
    ],
    "auto_install": False,
    "installable": True,
    "application": True,
}
# trigger update
