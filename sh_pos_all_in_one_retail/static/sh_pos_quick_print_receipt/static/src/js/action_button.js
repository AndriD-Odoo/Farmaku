odoo.define("sh_pos_quick_print_receipt.ActionButton", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");

    class QuickPrintButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-print-receipt", this.onClickPrintReceiptButton);
        }
        async onClickPrintReceiptButton() {
            console.log('Quick printed')
            const order = this.env.pos.get_order();
            if (order.get_orderlines().length > 0) {
                await this.showTempScreen('ShBillScreen');
            } else {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t('Nothing to Print'),
                    body: this.env._t('There are no order lines'),
                });
            }
        }
    }
    QuickPrintButton.template = "QuickPrintButton";
    ProductScreen.addControlButton({
        component: QuickPrintButton,
        condition: function () {
            return this.env.pos.config.sh_is_quick_receipt_print;
        },
    });
    Registries.Component.add(QuickPrintButton);

    return {
        QuickPrintButton,
    };
});
