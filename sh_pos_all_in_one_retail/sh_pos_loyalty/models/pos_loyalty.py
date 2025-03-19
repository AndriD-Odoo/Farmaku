# Copyright (C) Softhealer Technologies.

from odoo import fields, models, api, tools, _
from odoo.tools import float_is_zero
from odoo.exceptions import ValidationError
import psycopg2
import logging


class ShPosCoupon(models.Model):

    _name = 'sh.pos.coupon'
    _description = 'POS Coupon'

    @api.depends('order_ids')
    def _get_order(self):
        for rec in self:
            rec.order_count = len(rec.order_ids)

    name = fields.Char(string='Name', required='1')
    sh_coupon_code = fields.Char(string='Code', required='1')
    sh_coupon_active = fields.Boolean(string='Active')
    sh_coupon_for = fields.Selection([('specific_customer',
                                       'Specific Customer'), ('all', 'All')],
                                     string='Coupon Specific For', required='1',
                                     default='specific_customer')
    sh_coupon_partner = fields.Many2one('res.partner', string='Customer'
                                        )
    sh_coupon_expiry_date = fields.Date(string='Expiry Date',
                                        required='1')
    sh_coupon_applicable_date = fields.Date(string='Applicable From',
                                            required='1')
    sh_coupon_value = fields.Float(string='Coupon Value', required='1')
    sh_coupon_value_type = fields.Selection([('fixed', 'Fixed'),
                                             ('percentage', 'Percentage')], default='fixed', required='1', string='Coupon Value Type')
    sh_minimum_cart_amount = fields.Float(string='Minimum Cart Amount',
                                          required='1')
    sh_coupon_type = fields.Selection([('cart_amount_validation',
                                        'Use Cart Amount Validation'), ('partial_redeemption',
                                                                        'Use Partial Redeemption')], required='1',
                                      default='cart_amount_validation')
    sh_product_filter = fields.Selection([('specific_product',
                                           'Specific Product'), ('all', 'All')],
                                         string='Coupon Applied On', required='1',
                                         default='specific_product')
    sh_coupon_product_ids = fields.Many2many('product.product',
                                             string='Product')
    sequence_number = fields.Integer(string='Sequence Number',
                                     help='A session-unique sequence number for the order',
                                     default=1)
    uid = fields.Char(string='Number')
    max_discount = fields.Float(string='Maximum Discount')
    order_ids = fields.Many2many(
        'pos.order',
        'pos_order_coupon_rel',
        'order_id',
        'coupon_id',
        string='Orders')
    order_count = fields.Integer(
        string='Order Count',
        compute='_get_order')

    @api.onchange('sh_coupon_code', 'sh_coupon_applicable_date',
                  'sh_coupon_expiry_date')
    def _onchange_coupon_data(self):
        coupon_code_exist = self.search([('sh_coupon_code', '=',
                                          self.sh_coupon_code)])
        if coupon_code_exist:
            raise ValidationError(_('This Coupon Code is already exist. Please write some unique Coupon Code'
                                    ))
        if self.sh_coupon_expiry_date \
                and self.sh_coupon_applicable_date:
            if self.sh_coupon_applicable_date \
                    > self.sh_coupon_expiry_date:
                raise ValidationError(_('Coupon applicable date is less that coupon expiry date.'
                                        ))

    def _find_mail_template(self, force_confirmation_template=False):
        template_id = False

        template_id = self.env['ir.model.data'
                               ].xmlid_to_res_id('sh_pos_all_in_one_retail.email_template_pos_coupon', raise_if_not_found=False)

        return template_id

    def action_coupon_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''

        self.ensure_one()
        template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_template(template.lang,
                                             'sh.pos.coupon', self.ids[0])
        ctx = {
            'default_model': 'sh.pos.coupon',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': 'mail.mail_notification_light',
            'proforma': self.env.context.get('proforma', False),
            'sh_coupon_value_type': self.sh_coupon_value_type,
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    @api.model
    def create_from_ui(self, coupons):
        if coupons:

            # image is a dataurl, get the data after the comma

            for coupon in coupons:
                coupon_id = coupon.get('uid', False)
                if coupon_id:  # Modifying existing note
                    coupon_rec = self.search([('uid', '=',
                                               str(coupon_id))])
                    if coupon_rec:
                        coupon_rec.write(coupon)
                    else:
                        coupon_id = self.create(coupon).id
                else:
                    coupon_id = self.create(coupon).id
            return coupon_id

    def action_pos_order(self):
        return {
            'name': _('Orders'),
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.order_ids.ids)],
            'res_model': 'pos.order',
            'type': 'ir.actions.act_window',
            'context': {'create': False, 'active_test': False},
        }

class PosOrder(models.Model):

    _inherit = 'pos.order'

    coupon_ids = fields.Many2many(
        'sh.pos.coupon',
        'pos_order_coupon_rel',
        'coupon_id',
        'order_id',
        string='Coupons')

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)

        if ui_order.get('partner_id') and ui_order.get('loyalty_point') \
                and ui_order.get('pos_session_id'):
            config_id = self.env['pos.session'].search([('id', '=',
                                                         ui_order.get('pos_session_id'))]).config_id

            partner_obj = self.env['res.partner'].search([('id', '=',
                                                           ui_order.get('partner_id'))])
            sh_user_point_amount = partner_obj.sh_user_point_amount \
                + ui_order.get('loyalty_point') \
                * config_id.sh_loyalty_point_amount
            sh_user_point = partner_obj.sh_user_point \
                + ui_order.get('loyalty_point')
            partner_obj.write({'sh_user_point': sh_user_point,
                               'sh_user_point_amount': sh_user_point_amount})

        if ui_order.get('partner_id') \
                and ui_order.get('redeem_loyalty_point') \
                and ui_order.get('redeem_loyalty_amount'):
            partner_obj = self.env['res.partner'].search([('id', '=',
                                                           ui_order.get('partner_id'))])
            sh_user_point_amount = partner_obj.sh_user_point_amount \
                - float(ui_order.get('redeem_loyalty_amount'))
            sh_user_point = partner_obj.sh_user_point \
                - float(ui_order.get('redeem_loyalty_point'))
            partner_obj.write({'sh_user_point': sh_user_point,
                               'sh_user_point_amount': sh_user_point_amount})
        if ui_order.get('coupons'):
            coupon_ids = self.env['sh.pos.coupon'].search([
                ('sh_coupon_code', 'in', ui_order['coupons']),
            ])
            if coupon_ids:
                res.update({
                    'coupon_ids': [(6, 0, coupon_ids.ids)],
                })
        return res


class ResPartner(models.Model):

    _inherit = 'res.partner'

    sh_user_point = fields.Float(string='User Point')
    sh_user_point_amount = fields.Float(string='User Point Amount')
    sh_expiry_date = fields.Date(string='Validity of Redeem Points')
    sh_loyalty_card_no = fields.Char(string='Loyalty Card Number')


class PosConfig(models.Model):

    _inherit = 'pos.config'

    def _compute_coupon_access_rights(self):
        for rec in self:
            rec.sh_enable_create_coupon = self.env.ref(
                'sh_pos_all_in_one_retail.group_enable_create_coupon')
            rec.sh_enable_redeem_coupon = self.env.ref(
                'sh_pos_all_in_one_retail.group_enable_redeem_coupon')

    sh_enable_loyalty = fields.Boolean(string='Enable Loyalty')
    sh_enable_coupon = fields.Boolean(string='Enable Coupon')
    sh_loyalty_rule = fields.Many2one('sh.pos.loyalty',
                                      string='Loyalty Programme')
    sh_loyalty_point_amount = fields.Float(string='1 point = ? amount')
    sh_enable_create_coupon = fields.Many2one(
        'res.groups', compute='_compute_coupon_access_rights', string='POS - Enable Create Coupon')

    sh_enable_redeem_coupon = fields.Many2one(
        'res.groups', compute='_compute_coupon_access_rights', string='POS - Enable Redeem Coupon')


class ShPosLoyalty(models.Model):

    _name = 'sh.pos.loyalty'
    _description = 'POS Loyalty'

    name = fields.Char(string='Name')
    sh_point_per_order = fields.Float(string='Point Per Order')
    sh_point_per_product = fields.Float(string='Point Per Product')
    sh_loyalty_rule = fields.One2many('sh.pos.loyalty.rule',
                                      'sh_loyalty_id', string='Rules')
    sh_loyalty_reward = fields.One2many('sh.pos.loyalty.reward',
                                        'sh_loyalty_reward_id', string='Reward')


class ShPosLoyaltyRule(models.Model):

    _name = 'sh.pos.loyalty.rule'
    _description = 'POS Loyalty Rule'

    name = fields.Char(string='Rule Name')
    sh_rule_type = fields.Selection([('category', 'Category'),
                                     ('product', 'Product')],
                                    default='category', required=1)
    sh_point_per_product = fields.Float(string='Point Per Product')
    sh_loyalty_id = fields.Many2one('sh.pos.loyalty')
    sh_category_ids = fields.Many2many('pos.category', string='Category'
                                       )
    sh_product_ids = fields.Many2many('product.product',
                                      string='Product')


class ShPosLoyaltyReward(models.Model):

    _name = 'sh.pos.loyalty.reward'
    _description = 'POS Loyalty Reward'

    name = fields.Char(string='Reward Name')
    sh_loyalty_reward_id = fields.Many2one('sh.pos.loyalty')
    sh_reward_type = fields.Selection([('gift', 'Gift'), ('discount',
                                                          'Discount')], default='gift', required=1)
    sh_product_ids = fields.Many2one('product.product',
                                     string='Gift Product')
    sh_point_cost = fields.Float(string='Point Cost')
    sh_minimum_point = fields.Float(string='Minimum Points')
    sh_discount_percen = fields.Float(string='Discount (Percentage)')
