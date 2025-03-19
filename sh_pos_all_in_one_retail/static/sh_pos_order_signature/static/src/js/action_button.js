odoo.define("sh_pos_order_signature.ActionButton", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");

    class AddSignatureButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-add-signature", this.onClickTemplateLoad);
        }
        onClickTemplateLoad() {
            let { confirmed, payload } = this.showPopup("TemplateAddSignaturePopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }
    }
    AddSignatureButton.template = "AddSignatureButton";
    ProductScreen.addControlButton({
        component: AddSignatureButton,
        condition: function () {
            return this.env.pos.config.sh_enable_order_signature;
        },
    });
    Registries.Component.add(AddSignatureButton);

    return {
        AddSignatureButton,
    };
});
