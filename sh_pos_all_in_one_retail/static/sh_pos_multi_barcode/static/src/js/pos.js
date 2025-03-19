odoo.define("sh_pos_multi_barcode.pos", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var DB = require("point_of_sale.DB");

    models.load_models({
        model: "product.template.barcode",
        loaded: function (self, all_barcode) {
            _.each(all_barcode, function (each_barcode) {
                self.db.product_by_barcode[each_barcode.name] = self.db.product_by_id[each_barcode.product_id[0]];
            });
        },
    });
});
