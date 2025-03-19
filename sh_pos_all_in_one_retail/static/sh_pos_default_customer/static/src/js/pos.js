odoo.define("sh_pos_default_customer.pos", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");

    const DefaultProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                var self = this;
                var order = self.env.pos.get_order();
                if (!order.get_client()) {
                    if (self.env.pos.config.sh_enable_default_customer && self.env.pos.config.sh_default_customer_id) {
                        var set_partner = self.env.pos.db.get_partner_by_id(self.env.pos.config.sh_default_customer_id[0]);
                        if (set_partner) {
                            order.set_client(set_partner);
                        }
                    } else if (self.env.pos && self.env.pos.get_order()) {
                        self.env.pos.get_order().set_client(null);
                    }
                }
            }
        };

    Registries.Component.extend(ProductScreen, DefaultProductScreen);
});
