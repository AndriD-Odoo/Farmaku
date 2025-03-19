odoo.define("sh_pos_theme_responsive.payment_screen", function (require) {
    "use strict";

    const PaymentScreenNumpad = require("point_of_sale.PaymentScreenNumpad");
    const Registries = require("point_of_sale.Registries");
    const PaymentScreen = require("point_of_sale.PaymentScreen");

    const PosPaymentScreenNumpad = (PaymentScreenNumpad) =>
        class extends PaymentScreenNumpad {
            get currentOrder() {
                return this.env.pos.get_order();
            }
            async selectClient() {
                // IMPROVEMENT: This code snippet is repeated multiple times.
                // Maybe it's better to create a function for it.
                const currentClient = this.currentOrder.get_client();
                const { confirmed, payload: newClient } = await this.showTempScreen(
                    'ClientListScreen',
                    { client: currentClient }
                );
                if (confirmed) {
                    this.currentOrder.set_client(newClient);
                    this.currentOrder.updatePricelist(newClient);
                }
            }
            toggleIsToInvoice() {
                // click_invoice

                this.currentOrder.set_to_invoice(!this.currentOrder.is_to_invoice());
                this.render();
            }
        };

    Registries.Component.extend(PaymentScreenNumpad, PosPaymentScreenNumpad);

    const PosPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
            }
            mounted() {
                if (this.env.isMobile) {
                    $('.pos-content').addClass('sh_client_pos_content')
                }
            }
        };

    Registries.Component.extend(PaymentScreen, PosPaymentScreen);
});