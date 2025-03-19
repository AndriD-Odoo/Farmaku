odoo.define("sh_pos_logo.screens", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var core = require("web.core");
    var rpc = require("web.rpc");
    var Session = require("web.session");
    const Chrome = require("point_of_sale.Chrome");
    const Registries = require("point_of_sale.Registries");

    var QWeb = core.qweb;
    var _t = core._t;

    models.load_fields("res.company", ["sh_pos_global_header_logo", "global_header_logo", "sh_pos_global_logo", "global_receipt_logo"]);

    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        get_receipt_logo_url: function () {
            return window.location.origin + "/web/image?model=pos.config&field=receipt_logo&id=" + this.pos.config.id;
        },
        get_receipt_global_logo_url: function () {
            return window.location.origin + "/web/image?model=res.company&field=global_receipt_logo&id=" + this.pos.company.id;
        },
        export_for_printing: function () {
            var receipt = _super_Order.export_for_printing.apply(this, arguments);
            var order = this.pos.get_order();
            receipt["receipt_logo_url"] = order.get_receipt_logo_url();
            receipt["receipt_global_logo_url"] = order.get_receipt_global_logo_url();
            return receipt;
        },
        getOrderReceiptEnv: function () {
            var res = _super_Order.getOrderReceiptEnv.apply(this, arguments);
            res["receipt_logo_url"] = this.get_receipt_logo_url();
            res["receipt_global_logo_url"] = this.get_receipt_global_logo_url();
            return res;
        },
        get_header_logo_url: function (config) {
            return window.location.origin + "/web/image?model=pos.config&field=header_logo&id=" + config;
        },
        get_global_header_logo_url: function (company) {
            return window.location.origin + "/web/image?model=res.company&field=global_header_logo&id=" + company;
        },
    });
});
