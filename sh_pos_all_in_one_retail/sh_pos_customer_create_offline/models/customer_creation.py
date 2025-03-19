# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

from odoo import models, fields, api


class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_create_customer = fields.Boolean(string='Offline Create Customer ')


class PosPartner(models.Model):
    _inherit = 'res.partner'

    sh_cid = fields.Char(string='Sh cid')

    def pos_write_customer(self, dic):
        res = self.browse(dic.get('id'))

        res.write(dic)

        return True

    @api.model
    def create_offline_customer(self, partner):
        """ create or modify a partner from the point of sale ui.
            partner contains the partner's fields. """
        # image is a dataurl, get the data after the comma
        partner_ids = []
        for customer in partner:
            partner_dics = {}
            client = customer.get('currunt_client')
            if client:
                if client.get('image_1920'):
                    client['image_1920'] = client['image_1920'].split(',')[1]
                partner_id = client.pop('id', False)
                if partner_id:  # Modifying existing partner
                    self.browse(partner_id).write(client)
                else:
                    partner_id = self.create(client).id
                    customer['id'] = partner_id
                    partner_dics.update(
                        {'partner_id': partner_id, 'old_customer': customer})
                    partner_ids.append(partner_dics)
        return partner_ids
