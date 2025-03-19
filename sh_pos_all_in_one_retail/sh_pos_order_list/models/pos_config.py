# Copyright (C) Softhealer Technologies.

from odoo import fields, models, api, _
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    assigned_config = fields.Many2many(
        "pos.config", string=" Sh Assigned Config")
    sequence_number = fields.Integer(
        string='Sequence Number', help='A session-unique sequence number for the order', default=1)
    sh_uid = fields.Char(string='Number')
    sh_order_line_id = fields.Char(string='Number123')

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res['sh_uid'] = ui_order.get('sh_uid', False)
        res['sh_order_line_id'] = ui_order.get('sh_order_line_id', False)
        return res


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    sh_line_id = fields.Char(string='Number')


class PosConfig(models.Model):
    _inherit = "pos.config"

    sh_enable_order_reprint = fields.Boolean(string="Allow To Reprint Order")
    sh_enable_re_order = fields.Boolean(string="Allow To ReOrder")
    sh_enable_order_list = fields.Boolean(string="Enable Order List")
    sh_load_order_by = fields.Selection(
        [('all', 'All'), ('session_wise', 'Session Wise'), ('day_wise', 'Day Wise')], string="Load Order By", default='all', required="true")
    sh_session_wise_option = fields.Selection(
        [('current_session', 'Current Session'), ('last_no_session', 'Last No Of Session')], string="Session Of")
    sh_day_wise_option = fields.Selection(
        [('current_day', 'Current Day'), ('last_no_day', 'Last No Of Days')], string="Day Of")
    sh_last_no_days = fields.Integer(string="Last No Of Days")
    sh_last_no_session = fields.Integer(string="Last No Of Session")
    sh_how_many_order_per_page = fields.Integer(
        string="How Many Orders You Want to display Per Page ? ", default=30)
    sh_mode = fields.Selection(
        [('online_mode', 'Online'), ('offline_mode', 'Offline')], string="Update List", default='offline_mode')

    @api.constrains('sh_last_no_session', 'sh_last_no_days')
    def _check_validity_constrain(self):
        """ verifies if record.to_hrs is earlier than record.from_hrs. """
        for record in self:
            if self.sh_last_no_days < 0:
                raise ValidationError(
                    _('Last Number Of Days must be positive.'))
            if self.sh_last_no_session < 0:
                raise ValidationError(
                    _('Last Number Of Sessions must be positive.'))
