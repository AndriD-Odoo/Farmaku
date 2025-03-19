odoo.define("sh_pos_product_template.pos", function (require) {
    var models = require("point_of_sale.models");
    var rpc = require("web.rpc");
    var core = require("web.core");
    var QWeb = core.qweb;
    var _t = core._t;
    

    models.load_models({
        model: "pos.product.template",
        fields: ["name", "amount_total", "pos_product_template_ids"],
        domain: function (self) {
            return [["active", "=", true]];
        },
        loaded: function (self, pos_product_templates) {
            self.pos_product_templates = [];
            self.pos_product_templates = pos_product_templates;
        },
    });
    models.load_models({
        model: "pos.product.template.line",
        fields: ["name", "description", "ordered_qty", "unit_price", "discount", "product_uom", "price_subtotal", "pos_template_id"],
        domain: function (self) {
            return [];
        },
        loaded: function (self, pos_product_template_lines) {
            self.pos_product_template_lines = pos_product_template_lines;
            self.template_line_by_id = {};
            var data_list = [];

            _.each(pos_product_template_lines, function (line) {
                if (line.pos_template_id[0] in self.template_line_by_id) {
                    var temp_list = self.template_line_by_id[line.pos_template_id[0]];
                    temp_list.push(line);
                    self.template_line_by_id[line.pos_template_id[0]] = temp_list;
                } else {
                    data_list = [];
                    data_list.push(line);
                    self.template_line_by_id[line.pos_template_id[0]] = data_list;
                }
            });
        },
    });
});
