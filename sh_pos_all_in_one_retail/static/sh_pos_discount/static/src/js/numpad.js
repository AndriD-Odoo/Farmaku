odoo.define("sh_pos_discount.numpad", function (require) {
    "use strict";

    const NumpadWidget = require("point_of_sale.NumpadWidget");
    const Registries = require("point_of_sale.Registries");

    const PosNumpadWidgetScreen = (NumpadWidget) =>
        class extends NumpadWidget {
            constructor() {
                super(...arguments);
            }
            changeMode(mode) {
                var self = this;
                if (!this.hasPriceControlRights && mode === "price") {
                    return;
                }
                if (!this.hasManualDiscount && mode === "discount") {
                    return;
                }
                if (mode === "discount") {
                    // if (self.env.pos.config.sh_apply_custom_discount) {
                    if (self.env.pos.config.sh_line_discount_or_custom_discount == 'custom_discount' && self.env.pos.config.enable_custom_discount) {
                        if (this.env.pos.get_order() && this.env.pos.get_order().get_selected_orderline()) {
                            let { confirmed, payload } = self.showPopup("CustomDiscountPopupWidget");
                            if (confirmed) {
                            } else {
                                return;
                            }
                        }
                    }
                }
                this.trigger("set-numpad-mode", { mode });
            }
        };
    Registries.Component.extend(NumpadWidget, PosNumpadWidgetScreen);
});
