odoo.define("sh_pos_remove_cart_item.ActionButton", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");

    class RemoveAllItemButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-remove-all-item", this.onClickRemoveAllItemButton);
        }
        onClickRemoveAllItemButton() {
            var self = this;
            if (this.env.pos.get_order() && this.env.pos.get_order().get_orderlines() && this.env.pos.get_order().get_orderlines().length > 0) {
                var orderlines = this.env.pos.get_order().get_orderlines();
                _.each(orderlines, function (each_orderline) {
                    if (self.env.pos.get_order().get_orderlines()[0]) {
                        self.env.pos.get_order().remove_orderline(self.env.pos.get_order().get_orderlines()[0]);
                    }
                });
            } else {
                alert("No any product in cart");
            }
        }
    }
    RemoveAllItemButton.template = "RemoveAllItemButton";
    Registries.Component.add(RemoveAllItemButton);

    return {
        RemoveAllItemButton,
    };
});
