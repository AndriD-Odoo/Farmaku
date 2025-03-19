# Copyright 2015-TODAY ForgeFlow
# - Jordi Ballester Alomar
# Copyright 2015-TODAY Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License: LGPL-3 or later (https://www.gnu.org/licenses/lgpl.html).
{
    "name": "Custom Operating Unit",
    "summary": "Adds the concept of operating unit (OU) in stock management "
    "company",
    "version": "14.0.1.0.1",
    "author": "ForgeFlow, "
    "Serpent Consulting Services Pvt. Ltd.,"
    "Odoo Community Association (OCA),"
    "Arkana Solusi Digital (ASD)",
    "website": "https://github.com/OCA/operating-unit",
    "category": "Generic",
    "depends": ["operating_unit", "point_of_sale", "asb_update_sale_order"],
    "license": "LGPL-3",
    "data": [
        "security/stock_security.xml",
        "security/sale_security.xml",
        "data/stock_data.xml",
        "view/stock.xml",
        "view/sale_view.xml",
    ],
    "installable": True,
}
