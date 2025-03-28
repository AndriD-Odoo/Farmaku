# Copyright 2018 Creu Blanca
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class StockRequestOrder(models.Model):
    _name = "stock.request.order"
    _description = "Stock Request Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        # warehouse = None
        # if "warehouse_id" not in res and res.get("company_id"):
        #     warehouse = self.env["stock.warehouse"].search(
        #         [("company_id", "=", res["company_id"])], limit=1
        #     )
        # if warehouse:
        #     res["warehouse_id"] = warehouse.id
        #     res["location_id"] = warehouse.lot_stock_id.id
        return res

    def __get_request_order_states(self):
        return self.env["stock.request"]._get_request_states()

    def _get_request_order_states(self):
        return self.__get_request_order_states()

    def _get_default_requested_by(self):
        return self.env["res.users"].browse(self.env.uid)

    name = fields.Char(
        "Name",
        copy=False,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default="/",
    )
    state = fields.Selection(
        selection=_get_request_order_states,
        string="Status",
        copy=False,
        default="draft",
        index=True,
        readonly=True,
        tracking=True,
    )
    requested_by = fields.Many2one(
        "res.users",
        "Requested by",
        required=True,
        tracking=True,
        default=lambda s: s._get_default_requested_by(),
    )
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        "Warehouse",
        readonly=True,
        ondelete="cascade",
        required=True,
        states={"draft": [("readonly", False)]},
    )
    location_id = fields.Many2one(
        "stock.location",
        "Location",
        readonly=True,
        domain=[("usage", "in", ["internal", "transit"])],
        ondelete="cascade",
        required=True,
        states={"draft": [("readonly", False)]},
    )
    allow_virtual_location = fields.Boolean(
        related="company_id.stock_request_allow_virtual_loc", readonly=True
    )
    procurement_group_id = fields.Many2one(
        "procurement.group",
        "Procurement Group",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Moves created through this stock request will be put in this "
        "procurement group. If none is given, the moves generated by "
        "procurement rules will be grouped into one big picking.",
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self.env.company,
    )
    expected_date = fields.Datetime(
        "Expected Date",
        default=fields.Datetime.now,
        index=True,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Date when you expect to receive the goods.",
    )
    picking_policy = fields.Selection(
        [
            ("direct", "Receive each product when available"),
            ("one", "Receive all products at once"),
        ],
        string="Shipping Policy",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default="direct",
    )
    move_ids = fields.One2many(
        comodel_name="stock.move",
        compute="_compute_move_ids",
        string="Stock Moves",
        readonly=True,
    )
    picking_ids = fields.One2many(
        "stock.picking",
        compute="_compute_picking_ids",
        string="Pickings",
        readonly=True,
    )
    picking_count = fields.Integer(
        string="Delivery Orders", compute="_compute_picking_ids", readonly=True
    )
    stock_request_ids = fields.One2many(
        "stock.request", inverse_name="order_id", copy=True
    )
    stock_request_count = fields.Integer(
        string="Stock requests", compute="_compute_stock_request_count", readonly=True
    )

    _sql_constraints = [
        ("name_uniq", "unique(name, company_id)", "Stock Request name must be unique")
    ]

    @api.depends("stock_request_ids.allocation_ids")
    def _compute_picking_ids(self):
        for record in self:
            record.picking_ids = record.stock_request_ids.mapped("picking_ids")
            record.picking_count = len(record.picking_ids)

    @api.depends("stock_request_ids")
    def _compute_move_ids(self):
        for record in self:
            record.move_ids = record.stock_request_ids.mapped("move_ids")

    @api.depends("stock_request_ids")
    def _compute_stock_request_count(self):
        for record in self:
            record.stock_request_count = len(record.stock_request_ids)

    @api.onchange("requested_by")
    def onchange_requested_by(self):
        self.change_childs()

    @api.onchange("expected_date")
    def onchange_expected_date(self):
        self.change_childs()

    @api.onchange("picking_policy")
    def onchange_picking_policy(self):
        self.change_childs()

    @api.onchange("location_id")
    def onchange_location_id(self):
        if self.location_id:
            loc_wh = self.location_id.get_warehouse()
            if loc_wh and self.warehouse_id != loc_wh:
                self.warehouse_id = loc_wh
                self.with_context(no_change_childs=True).onchange_warehouse_id()
        self.change_childs()

    @api.onchange("allow_virtual_location")
    def onchange_allow_virtual_location(self):
        if self.allow_virtual_location:
            return {"domain": {"location_id": []}}

    @api.onchange("warehouse_id")
    def onchange_warehouse_id(self):
        if self.warehouse_id:
            # search with sudo because the user may not have permissions
            loc_wh = self.location_id.get_warehouse()
            if self.warehouse_id != loc_wh:
                self.location_id = self.warehouse_id.wh_input_stock_loc_id
                self.with_context(no_change_childs=True).onchange_location_id()
            if self.warehouse_id.company_id != self.company_id:
                self.company_id = self.warehouse_id.company_id
                self.with_context(no_change_childs=True).onchange_company_id()
        self.change_childs()

    @api.onchange("procurement_group_id")
    def onchange_procurement_group_id(self):
        self.change_childs()

    @api.onchange("company_id")
    def onchange_company_id(self):
        # if self.company_id and (
        #     not self.warehouse_id or self.warehouse_id.company_id != self.company_id
        # ):
        #     self.warehouse_id = self.env["stock.warehouse"].search(
        #         [("company_id", "=", self.company_id.id)], limit=1
        #     )
        #     self.with_context(no_change_childs=True).onchange_warehouse_id()
        self.change_childs()
        return {"domain": {"warehouse_id": [("company_id", "=", self.company_id.id)]}}

    def change_childs(self):
        if not self._context.get("no_change_childs", False):
            for line in self.stock_request_ids:
                line.warehouse_id = self.warehouse_id
                line.location_id = self.location_id
                line.company_id = self.company_id
                line.picking_policy = self.picking_policy
                line.expected_date = self.expected_date
                line.requested_by = self.requested_by
                line.procurement_group_id = self.procurement_group_id

    def action_confirm(self):
        self.mapped("stock_request_ids").action_confirm()
        self.write({"state": "open"})
        return True

    def action_draft(self):
        self.mapped("stock_request_ids").action_draft()
        self.write({"state": "draft"})
        return True

    def action_cancel(self):
        self.mapped("stock_request_ids").action_cancel()
        self.write({"state": "cancel"})
        return True

    def action_done(self):
        self.write({"state": "done"})
        return True

    def check_done(self):
        for rec in self:
            if not rec.stock_request_ids.filtered(lambda r: r.state != "done"):
                rec.action_done()
        return

    def action_view_transfer(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "stock.action_picking_tree_all"
        )

        pickings = self.mapped("picking_ids")
        if len(pickings) > 1:
            action["domain"] = [("id", "in", pickings.ids)]
        elif pickings:
            action["views"] = [(self.env.ref("stock.view_picking_form").id, "form")]
            action["res_id"] = pickings.id
        return action

    def action_view_stock_requests(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "stock_request.action_stock_request_form"
        )
        if len(self.stock_request_ids) > 1:
            action["domain"] = [("order_id", "in", self.ids)]
        elif self.stock_request_ids:
            action["views"] = [
                (self.env.ref("stock_request.view_stock_request_form").id, "form")
            ]
            action["res_id"] = self.stock_request_ids.id
        return action

    @api.model
    def create(self, vals):
        upd_vals = vals.copy()
        if upd_vals.get("name", "/") == "/":
            upd_vals["name"] = self.env["ir.sequence"].next_by_code(
                "stock.request.order"
            )
        return super().create(upd_vals)

    def unlink(self):
        if self.filtered(lambda r: r.state != "draft"):
            raise UserError(_("Only orders on draft state can be unlinked"))
        return super().unlink()

    @api.constrains("warehouse_id", "company_id")
    def _check_warehouse_company(self):
        if any(
            request.warehouse_id.company_id != request.company_id for request in self
        ):
            raise ValidationError(
                _(
                    "The company of the stock request must match with "
                    "that of the warehouse."
                )
            )

    @api.constrains("location_id", "company_id")
    def _check_location_company(self):
        if any(
            request.location_id.company_id
            and request.location_id.company_id != request.company_id
            for request in self
        ):
            raise ValidationError(
                _(
                    "The company of the stock request must match with "
                    "that of the location."
                )
            )

    @api.model
    def _create_from_product_multiselect(self, products):
        if not products:
            return False
        if products._name not in ("product.product", "product.template"):
            raise ValidationError(
                _("This action only works in the context of products")
            )
        if products._name == "product.template":
            # search instead of mapped so we don't include archived variants
            products = self.env["product.product"].search(
                [("product_tmpl_id", "in", products.ids)]
            )
        expected = self.default_get(["expected_date"])["expected_date"]
        try:
            order = self.env["stock.request.order"].create(
                dict(
                    expected_date=expected,
                    stock_request_ids=[
                        (
                            0,
                            0,
                            dict(
                                product_id=product.id,
                                product_uom_id=product.uom_id.id,
                                product_uom_qty=1.0,
                                expected_date=expected,
                            ),
                        )
                        for product in products
                    ],
                )
            )
        except AccessError:
            # TODO: if there is a nice way to hide the action from the
            # Action-menu if the user doesn't have the necessary rights,
            # that would be a better way of doing this
            raise UserError(
                _(
                    "Unfortunately it seems you do not have the necessary rights "
                    "for creating stock requests. Please contact your "
                    "administrator."
                )
            )
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "stock_request.stock_request_order_action"
        )
        action["views"] = [
            (self.env.ref("stock_request.stock_request_order_form").id, "form")
        ]
        action["res_id"] = order.id
        return action

    def button_done(self):
        self.mapped('stock_request_ids').filtered(lambda r: r.state == 'open').action_done()
