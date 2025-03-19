from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    font = fields.Selection(selection_add=[
        ('Arial', 'Arial'),
        ('Calibri', 'Calibri'),
        ('Courier New', 'Courier New'),
        ('Times New Roman', 'Times New Roman'),
    ], default='Courier New')
    pbf_permit_number = fields.Char(related='partner_id.pbf_permit_number', readonly=False)
    cdob = fields.Char(related='partner_id.cdob', readonly=False)

    def __init__(self, pool, cr):
        query = """
            UPDATE
                res_company
            SET
                font = 'Courier New',
                primary_color = '#000000',
                secondary_color = '#000000',
                external_report_layout_id = (SELECT view_id FROM report_layout WHERE name = 'Boxed' LIMIT 1)
            WHERE
                font != 'Courier New'
                OR primary_color != '#000000'
                OR secondary_color != '#000000'
                OR external_report_layout_id != (SELECT view_id FROM report_layout WHERE name = 'Boxed' LIMIT 1)
        """
        cr.execute(query=query)
        return super(ResCompany, self).__init__(pool, cr)

    def _get_sequence(self, name, code, pref, company_id, padding=6):
        # archive other sequences
        sequence_ids = self.env['ir.sequence'].sudo().search([
            ('code', '=', code),
            ('company_id', '=', False)
        ])
        if sequence_ids:
            sequence_ids.write({
                'active': False
            })
        sequence_id = self.env['ir.sequence'].sudo().search([
            ('code', '=', code),
            ('company_id', '=', company_id)
        ], limit=1)
        if not sequence_id:
            sequence_id = self.env['ir.sequence'].sudo().create({
                'name': name,
                'code': code,
                'implementation': 'no_gap',
                'prefix': pref,
                'padding': padding,
                'company_id': company_id
            })
        return sequence_id

    def _update_sequence(self):
        company_codes = {
            1: 'S',
            2: 'N',
            3: 'F',
        }
        for comp_id, comp_code in company_codes.items():
            # PO
            pref = f'P{comp_code}%(y)s%(month)s'
            self._get_sequence(
                name='PO',
                code='purchase.order',
                pref=pref,
                company_id=comp_id,
                padding=6
            )
            # SO
            pref = f'S{comp_code}%(y)s%(month)s'
            self._get_sequence(
                name='SO',
                code='sale.order',
                pref=pref,
                company_id=comp_id,
                padding=7
            )
            # operation types
            warehouse_ids = self.env['stock.warehouse'].sudo().search([
                ('company_id', '=', comp_id)
            ])
            for warehouse_id in warehouse_ids:
                in_type_id = warehouse_id.in_type_id
                int_type_id = warehouse_id.int_type_id
                pick_type_id = warehouse_id.pick_type_id
                pack_type_id = warehouse_id.pack_type_id
                out_type_id = warehouse_id.out_type_id

                pref = f'{warehouse_id.code}/IN/%(y)s%(month)s'
                in_type_id.sequence_id.sudo().write({
                    'prefix': pref,
                    'padding': 6,
                    'number_next_actual': 1,
                })
                pref = f'{warehouse_id.code}/INT/%(y)s%(month)s'
                int_type_id.sequence_id.sudo().write({
                    'prefix': pref,
                    'padding': 6,
                    'number_next_actual': 1,
                })
                pref = f'{warehouse_id.code}/PICK/%(y)s%(month)s'
                pick_type_id.sequence_id.sudo().write({
                    'prefix': pref,
                    'padding': 7,
                    'number_next_actual': 1,
                })
                pref = f'{warehouse_id.code}/PACK/%(y)s%(month)s'
                pack_type_id.sequence_id.sudo().write({
                    'prefix': pref,
                    'padding': 7,
                    'number_next_actual': 1,
                })
                pref = f'{warehouse_id.code}/OUT/%(y)s%(month)s'
                out_type_id.sequence_id.sudo().write({
                    'prefix': pref,
                    'padding': 7,
                    'number_next_actual': 1,
                })
