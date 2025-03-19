# -*- coding: utf-8 -*-
{
    "name": "Base Extended",
    "summary": """
        Extend function of base module
    """,
    "description": """
        
    """,
    "author": "Odoo Freelancer",
    "website": "",
    "category": "Base",
    "version": "14.0.1.0.0",
    "depends": [
        "base",
        "mail",
        "web",
        "stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/decimal_precision.xml",
        "data/res_country.xml",
        "data/report_paperformat.xml",
        "data/ir_cron.xml",
        "views/res_partner_views.xml",
        "views/templates.xml",
        "views/report_templates.xml",
        "views/report_templates_custom.xml",
        "views/stock_warehouse_views.xml",
        "views/res_company_views.xml",
    ],
    "demo": [

    ],
}
