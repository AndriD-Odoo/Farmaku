# -*- coding: utf-8 -*-
{
    'name': "Farmaku Invoice Recap",

    'summary': """
        Custom feature to import Settlement Data from the Marketplace and Create Invoice Recap""",

    'description': """
        Placeholder for the long description
    """,

    'author': "Harvey F. Tanauma",
    # 'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.05',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        # 'crm',
        'sales_team',
        'product',
        'asb_rest_api',
    ],

    # always loaded
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        # 'views/config_settings.xml',
        'views/views.xml',
        'views/inv_recap.xml',
        'views/crm_team_views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
