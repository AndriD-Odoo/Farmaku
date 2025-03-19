odoo.define("sh_pos_line_pricelist.orderline", function (require) {
    "use strict";

    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");
    const { useBarcodeReader } = require("point_of_sale.custom_hooks");
    const { useListener } = require("web.custom_hooks");
    const ProductsWidget = require("point_of_sale.ProductsWidget");

    const ProductPricelistScreen = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                useListener("click-pricelist-icon", this.on_click_pricelist_icon);
            }
            async on_click_pricelist_icon(event) {
                var self = this;
                setTimeout(() => {
                    let { confirmed, payload } = self.showPopup("PriceListPopupWidget");
                    if (confirmed) {
                    } else {
                        return;
                    }
                }, 100);
            }
            _setValue(val) {

                if (this.currentOrder.get_selected_orderline()) {
                    if (this.state.numpadMode === "quantity") {
                        this.currentOrder.get_selected_orderline().set_quantity(val);
                    } else if (this.state.numpadMode === "discount") {
                        this.currentOrder.get_selected_orderline().set_discount(val);
                    } else if (this.state.numpadMode === "price") {
                        var selected_orderline = this.currentOrder.get_selected_orderline();
                        selected_orderline.is_added = true;
                        selected_orderline.price_manually_set = true;
                        selected_orderline.set_unit_price(val);
                    }
                    if (this.env.pos.config.iface_customer_facing_display) {
                        this.env.pos.send_current_order_to_customer_facing_display();
                    }
                }
            }
        };

    Registries.Component.extend(ProductScreen, ProductPricelistScreen);
});
