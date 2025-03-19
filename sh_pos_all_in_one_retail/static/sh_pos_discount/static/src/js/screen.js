odoo.define("sh_pos_discount.screen", function (require) {
    "use strict";

    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");
    const { useBarcodeReader } = require("point_of_sale.custom_hooks");
    const { useListener } = require("web.custom_hooks");
    const ProductsWidget = require("point_of_sale.ProductsWidget");

    const DiscountProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                useListener("click-discount-icon", this.on_click_show_discount);
            }
            async on_click_show_discount(event) {
                
                var self = this;
                let { confirmed, payload } = self.showPopup("CustomDiscountPopupWidget");
                if (confirmed) {
                } else {
                    return;
                }
            }
        };

    Registries.Component.extend(ProductScreen, DiscountProductScreen);
});
