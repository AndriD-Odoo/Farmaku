from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _compute_effective_date(self):
        super(PurchaseOrder, self)._compute_effective_date()
        for order in self:
            pickings = order.picking_ids.filtered(
                lambda x: x.state == 'done' and x.location_dest_id.usage == 'internal' and x.date_done)
            order.effective_date = max(pickings.mapped('date_done'), default=False)

    def _update_effective_date(self):
        query = """
            UPDATE
                purchase_order po
            SET
                effective_date = sp.date_done,
                date_planned = sp.date_done
            FROM
                (
                    SELECT 
                        po.id as purchase_id,
                        MAX(sp.date_done) as date_done
                    FROM
                        purchase_order_line pol
                    LEFT JOIN
                        purchase_order po ON po.id = pol.order_id
                    LEFT JOIN
                        stock_move sm ON sm.purchase_line_id = pol.id
                    LEFT JOIN
                        stock_picking sp ON sp.id = sm.picking_id
                    WHERE
                        sp.state = 'done'
                    GROUP BY
                        po.id
                ) AS sp
            WHERE
                po.id = sp.purchase_id
                AND sp.date_done IS NOT null
        """
        self.env.cr.execute(query)

    @api.model
    def _get_picking_type(self, company_id):
        if self.env.user.property_warehouse_id:
            picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'incoming'), ('warehouse_id', '=', self.env.user.property_warehouse_id.id)])
            if not picking_type:
                picking_type = self.env['stock.picking.type'].search(
                    [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
            return picking_type[:1]
        else:
            return super(PurchaseOrder, self)._get_picking_type(company_id)
