{
    'name': 'Recon Bank - Invoice',
    'author': 'A.D',
    'version': '0.1',
    'depends': ['account', 'account_accountant'],
    'data': [
       'security/ir.model.access.csv',
       #views
       'views/account_move_views.xml',
       #wizard
       'wizard/wizard_import_bank_excel_views.xml',

    ],
    'sequence': 1,
    'auto_install': False,
    'installable': True,
    'application': True,
    'category': '- Farmaku',
    'summary': 'Rekonsiliasi Bank Statement via excel dengan cross match value',
    'website': 'https://www.farmaku.com/',
    'description': '-'
}
