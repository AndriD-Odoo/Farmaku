odoo.define("sh_pos_discount.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");

    models.load_models({
        model: "pos.discount",
        loaded: function (self, discounts) {
            self.db.add_discount(discounts);
        },
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            this.line_discount = "";
            this.line_discount_code = "";
            _super_orderline.initialize.call(this, attr, options);
        },
        set_line_discount: function (line_discount) {
            this.set("line_discount", line_discount);
        },
        get_line_discount: function () {
            return this.get("line_discount");
        },
        set_line_discount_code: function (line_discount_code) {
            this.set("line_discount_code", line_discount_code);
            if (line_discount_code && line_discount_code.length == 1) {
                this.set("display_line_discount_code", line_discount_code[0]);
            } else {
                var display_code_string = "";
                for (var i = 0; i < line_discount_code.length; i++) {
                    if (i == line_discount_code.length - 1) {
                        display_code_string = display_code_string + line_discount_code[i];
                    } else {
                        display_code_string = display_code_string + line_discount_code[i] + " , ";
                    }
                }
                this.set("display_line_discount_code", display_code_string);
            }
        },
        get_line_discount_code: function () {
            return this.get("line_discount_code");
        },
        export_for_printing: function () {
            var self = this;
            var lines = _super_orderline.export_for_printing.call(this);
            var new_attr = {
                line_discount: this.get_line_discount() || false,
            };
            $.extend(lines, new_attr);
            return lines;
        },
        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.apply(this, arguments);
            json.line_discount = this.get("line_discount") || null;
            json.sh_discount_code = this.get("display_line_discount_code") || null;
            return json;
        },
    });
});
