# -*- coding: utf-8 -*-
{
    "name": "API Sale",
    "summary": """
        Send sale order and POS data to FE
    """,
    "description": """

    """,
    "author": "Odoo Freelancer",
    "website": "",
    "category": "Sale",
    "version": "14.0.1.0.0",
    "depends": [
        "base",
        "sale",
        "point_of_sale",
        "sale_stock",
    ],
    "data": [
        "data/ir_cron.xml",
        "data/ir_config_parameter.xml",
    ],
    "demo": [

    ],
}
