from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import dateutil.parser
from dateutil import tz


import logging
_logger = logging.getLogger(__name__)

import base64
import json
import requests

def set_tz(date_convert, tz_from, tz_to):
    res = date_convert
    if date_convert:
        res = date_convert.replace(tzinfo=tz.gettz(tz_from))
        res = res.astimezone(tz.gettz(tz_to))
    return res

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _default_operating_unit(self):
        return self.env.user.default_operating_unit_id.id

    operating_unit_id = fields.Many2one(
        comodel_name="operating.unit",
        string="Operating Unit",
        # default=_default_operating_unit,
        readonly=True,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
    )

    def update_operating_unit_so(self):
        operating_unit = self.warehouse_id.operating_unit_id
        # warehouse = self.warehouse_id
        # parent_location = self.view_location_id
        # locations = self.env["stock.location"].search(
        #     [("id", "child_of", [parent_location.id]), ("usage", "=", "internal")]
        # )
        if operating_unit:
            query = """update sale_order set operating_unit_id = %s where
            id in %s"""
            self._cr.execute(
                query, (operating_unit.id, tuple(self.ids))
            )
        return True

    # @api.onchange("team_id")
    # def onchange_team_id(self):
    #     if self.team_id:
    #         self.operating_unit_id = self.team_id.operating_unit_id

    # @api.onchange("operating_unit_id")
    # def onchange_operating_unit_id(self):
    #     if self.team_id and self.team_id.operating_unit_id != self.operating_unit_id:
    #         self.team_id = False

    # @api.constrains("team_id", "operating_unit_id")
    # def _check_team_operating_unit(self):
    #     for rec in self:
    #         if rec.team_id and rec.team_id.operating_unit_id != rec.operating_unit_id:
    #             raise ValidationError(
    #                 _(
    #                     "Configuration error. The Operating "
    #                     "Unit of the sales team must match "
    #                     "with that of the quote/sales order."
    #                 )
    #             )

    @api.constrains("operating_unit_id", "company_id")
    def _check_company_operating_unit(self):
        for rec in self:
            if (
                rec.company_id
                and rec.operating_unit_id
                and rec.company_id != rec.operating_unit_id.company_id
            ):
                raise ValidationError(
                    _(
                        "Configuration error. The Company in "
                        "the Sales Order and in the Operating "
                        "Unit must be the same."
                    )
                )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    operating_unit_id = fields.Many2one(
        related="order_id.operating_unit_id", string="Operating Unit"
    )


class SaleReport(models.Model):

    _inherit = "sale.report"

    operating_unit_id = fields.Many2one("operating.unit", "Operating Unit")

    def _query(self, with_clause="", fields=False, groupby="", from_clause=""):  # noqa
        if not fields:
            fields = {}
        fields["operating_unit_id"] = ", s.operating_unit_id as operating_unit_id"
        groupby += ", s.operating_unit_id"
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
