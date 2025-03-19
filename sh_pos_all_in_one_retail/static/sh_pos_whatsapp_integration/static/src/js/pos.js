odoo.define("sh_pos_whatsapp_integration.WhatsappMessagePopup", function (require) {
    "use strict";

    const { useState, useSubEnv } = owl.hooks;
    const PosComponent = require("point_of_sale.PosComponent");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    const Registries = require("point_of_sale.Registries");

    class WhatsappMessagePopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            useSubEnv({ attribute_components: [] });
        }
    }
    WhatsappMessagePopup.template = "WhatsappMessagePopup";

    Registries.Component.add(WhatsappMessagePopup);

    return {
        WhatsappMessagePopup,
    };
});

odoo.define("sh_pos_whatsapp_integration.ReceiptScreen", function (require) {
    "use strict";
    const ReceiptScreen = require("point_of_sale.ReceiptScreen");
    const Registries = require("point_of_sale.Registries");
    const { useBarcodeReader } = require("point_of_sale.custom_hooks");
    const { useListener } = require("web.custom_hooks");

    const WPReceiptScreen = (ReceiptScreen) =>
        class extends ReceiptScreen {
            constructor() {
                super(...arguments);
                useListener("click-send_wp", this.on_click_send_wp);
                useListener("click-send_wp_dierct", this.on_click_send_wp_direct);
            }
            async on_click_send_wp_direct(event) {
                var message = "";
                var self = this;

                const partner = this.currentOrder.get_client();
                if (partner && partner.mobile) {
                    var mobile = partner.mobile;
                    var order = this.currentOrder;
                    var receipt = this.currentOrder.export_for_printing();
                    var orderlines = this.currentOrder.get_orderlines();
                    var paymentlines = this.currentOrder.get_paymentlines();
                    message +=
                        "Dear " +
                        partner.name +
                        "," +
                        "%0A%0A" +
                        "Here is the order " +
                        "*" +
                        receipt.name +
                        "*" +
                        " amounting in " +
                        "*" +
                        receipt.total_with_tax.toFixed(2) +
                        "*" +
                        "" +
                        receipt.currency.symbol +
                        " from " +
                        receipt.company.name +
                        "%0A%0A";
                    if (receipt.orderlines.length > 0) {
                        message += "Following is your order details." + "%0A";
                        _.each(receipt.orderlines, function (orderline) {
                            message += "%0A" + "*" + orderline.product_name + "*" + "%0A" + "*Qty:* " + orderline.quantity + "%0A" + "*Price:* " + orderline.price + "" + receipt.currency.symbol + "%0A";
                            if (orderline.discount > 0) {
                                message += "*Discount:* " + orderline.discount + "%25" + "%0A";
                            }
                        });
                        message += "________________________" + "%0A";
                    }
                    message += "*" + "Total Amount:" + "*" + "%20" + receipt.total_with_tax.toFixed(2) + "" + receipt.currency.symbol;
                    if (this.env.pos.user.sign) {
                        message += "%0A%0A%0A" + this.env.pos.user.sign;
                    }
                    $(".default-view").append('<a class="wp_url" target="blank" href=""><span></span></a>');
                    var href = "https://web.whatsapp.com/send?l=&phone=" + mobile + "&text=" + message.replace('&','%26');
                    $(".wp_url").attr("href", href);
                    $(".wp_url span").trigger("click");
                }
            }
            async on_click_send_wp(event) {
                var message = "";
                var self = this;

                const partner = this.currentOrder.get_client();
                if (partner && partner.mobile) {
                    var mobile = partner.mobile;
                    var order = this.currentOrder;
                    var receipt = this.currentOrder.export_for_printing();
                    var orderlines = this.currentOrder.get_orderlines();
                    var paymentlines = this.currentOrder.get_paymentlines();

                    message +=
                        "Dear " +
                        partner.name +
                        "," +
                        "%0A%0A" +
                        "Here is the order " +
                        "*" +
                        receipt.name +
                        "*" +
                        " amounting in " +
                        "*" +
                        receipt.total_with_tax.toFixed(2) +
                        "*" +
                        "" +
                        receipt.currency.symbol +
                        " from " +
                        receipt.company.name +
                        "%0A%0A";
                    if (receipt.orderlines.length > 0) {
                        message += "Following is your order details." + "%0A";
                        _.each(receipt.orderlines, function (orderline) {
                            message += "%0A" + "*" + orderline.product_name + "*" + "%0A" + "*Qty:* " + orderline.quantity + "%0A" + "*Price:* " + orderline.price + "" + receipt.currency.symbol + "%0A";
                            if (orderline.discount > 0) {
                                message += "*Discount:* " + orderline.discount + "%25" + "%0A";
                            }
                        });
                        message += "________________________" + "%0A";
                    }
                    message += "*" + "Total Amount:" + "*" + "%20" + receipt.total_with_tax.toFixed(2) + "" + receipt.currency.symbol;
                    if (this.env.pos.user.sign) {
                        message += "%0A%0A%0A" + this.env.pos.user.sign;
                    }

                    const { confirmed } = await this.showPopup("WhatsappMessagePopup", {
                        mobile_no: partner.mobile,
                        message: message.replace('&','%26'),
                        confirmText: "Send",
                        cancelText: "Cancel",
                    });
                    if (confirmed) {
                        var text_msg = $('textarea[name="message"]').val();
                        var mobile = $(".mobile_no").val();
                        if (text_msg && mobile) {
                            var href = "https://web.whatsapp.com/send?l=&phone=" + mobile + "&text=" + text_msg.replace('&','%26');
                            $(".wp_url").attr("href", href);
                            $(".wp_url span").trigger("click");
                        } else {
                            alert("Please Enter Message.");
                        }
                    }
                }
            }
        };

    Registries.Component.extend(ReceiptScreen, WPReceiptScreen);

    return ReceiptScreen;
});
odoo.define("sh_pos_whatsapp_integration.ClientListScreen", function (require) {
    "use strict";
    const ClientListScreen = require("point_of_sale.ClientListScreen");
    const Registries = require("point_of_sale.Registries");
    const { useBarcodeReader } = require("point_of_sale.custom_hooks");
    const { useListener } = require("web.custom_hooks");

    const WPClientListScreen = (ClientListScreen) =>
        class extends ClientListScreen {
            constructor() {
                super(...arguments);
                useListener("click-send_wp", this.on_click_send_wp);
            }
            async on_click_send_wp(event) {
                var message = "";
                var self = this;
                if (this.env.pos.user.sign) {
                    message += "%0A%0A%0A" + this.env.pos.user.sign;
                }
                const partner = event.detail;

                const { confirmed } = await this.showPopup("WhatsappMessagePopup", {
                    mobile_no: partner.mobile,
                    message: message.replace('&','%26'),
                    confirmText: "Send",
                    cancelText: "Cancel",
                });
                if (confirmed) {
                    var text_msg = $('textarea[name="message"]').val();
                    var mobile = $(".mobile_no").val();
                    if (text_msg && mobile) {
                        var href = "https://web.whatsapp.com/send?l=&phone=" + mobile + "&text=" + text_msg.replace('&','%26');
                        $(".wp_url").attr("href", href);
                        $(".wp_url span").trigger("click");
                    } else {
                        alert("Please Enter Message.");
                    }
                }
            }
        };

    Registries.Component.extend(ClientListScreen, WPClientListScreen);

    return ClientListScreen;
});

odoo.define("sh_pos_whatsapp_integration.screens", function (require) {
    "use strict";

    var models = require("point_of_sale.models");

    var core = require("web.core");
    var rpc = require("web.rpc");
    var DB = require("point_of_sale.DB");

    models.load_fields("res.users", ["sign"]);
    models.load_fields("res.partner", ["lang", "mobile"]);

});
