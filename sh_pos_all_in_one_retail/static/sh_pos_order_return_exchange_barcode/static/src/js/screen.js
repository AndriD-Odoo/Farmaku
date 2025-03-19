odoo.define("sh_pos_order_return_exchange_barcode.screen", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const PaymentScreen = require("point_of_sale.PaymentScreen");

    const PosResPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
            }
            async validateOrder(isForceValidate) {
                var self = this;
                super.validateOrder(isForceValidate);
                var order_barcode = self.env.pos.get_order().uid.split("-");
                self.env.pos.get_order().barcode = "";
                var sh_line_id = [];
                _.each(order_barcode, function (splited_barcode) {
                    self.env.pos.get_order().barcode = self.env.pos.get_order().barcode + splited_barcode;
                });
                self.env.pos.db.order_by_uid[self.env.pos.get_order().export_as_JSON().sh_uid] = self.env.pos.get_order().export_as_JSON();
                self.env.pos.db.order_by_barcode[self.env.pos.get_order().barcode] = self.env.pos.get_order().export_as_JSON();
                _.each(self.env.pos.get_order().export_as_JSON().lines, function (each_line) {
                    self.env.pos.db.order_line_by_uid[each_line[2].sh_line_id] = each_line[2];
                    sh_line_id.push(each_line[2].sh_line_id);
                });
                self.env.pos.get_order()["sh_line_id"] = sh_line_id;
            }
        };
    Registries.Component.extend(PaymentScreen, PosResPaymentScreen);
});
