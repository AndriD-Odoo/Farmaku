odoo.define("sh_pos_order_signature.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        set_signature_date: function (signature_date) {
            this.set("signature_date", signature_date);
        },
        get_signature_date: function () {
            return this.get("signature_date") || false;
        },
        set_signature_name: function (signature_name) {
            this.set("signature_name", signature_name);
        },
        get_signature_name: function () {
            return this.get("signature_name");
        },
        set_signature: function (signature) {
            this.set("signature", signature);
        },
        get_signature: function () {
            return this.get("signature") || false;
        },
        export_as_JSON: function () {
            var submitted_order = _super_order.export_as_JSON.call(this);
            var new_val = {
                signature: this.get_signature(),
                signature_name: this.get_signature_name(),
                signature_date: this.get_signature_date(),
            };
            $.extend(submitted_order, new_val);
            return submitted_order;
        },
        export_for_printing: function () {
            var self = this;
            var orders = _super_order.export_for_printing.call(this);
            var new_val = {
                signature: this.get_signature(),
                signature_name: this.get_signature_name(),
                signature_date: this.get_signature_date(),
            };
            $.extend(orders, new_val);
            return orders;
        },
    });
});
