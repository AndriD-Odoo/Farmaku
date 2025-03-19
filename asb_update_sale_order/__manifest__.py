# -*- coding: utf-8 -*-
{
    "name": "Sale Order",
    "description": """
        Module for bulk import Sale Order from marketplace
    """,
    "author": "Arkana Solusi Bisnis",
    "website": "https://www.arkana.co.id/",
    "category": "Backend",
    "version": "14.0.1.0.0",
    "depends": [
        "base",
        "sale",
        "account",
        "sale_stock",
        "asb_base_farmaku",
        "asb_rest_api"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/status_mkp_data.xml",
        "views/sale_view.xml",
        "views/picking_view.xml",
        "views/move_view.xml",
        "views/notif_import_view.xml",
        "views/shop_name_conf.xml",
        "views/status_mkp_view.xml",
        "views/crm_team_view.xml",
        "wizard/sale_wizard.xml",
    ],
    "demo": [

    ],
    "installable": True,
    "application": True,
}
