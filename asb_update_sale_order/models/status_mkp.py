from odoo import models, fields, api, _

class StatusMkp(models.Model):
    _name = 'status.mkp'
    _description = 'Status Marketplace'
    
    name = fields.Char(string='Nama')
    status = fields.Char(string='Status')
    channel = fields.Char(string='Channel')
    status_type = fields.Selection([
        ('open', 'Open'),
        ('process', 'Process'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='Status Type'
    , help='''
    - Open = Create SO, DO, Inv
    - Process = Process in warehouse
    - Done = Order in delivery or order done
    - Cancel = Order canceled
    ''')