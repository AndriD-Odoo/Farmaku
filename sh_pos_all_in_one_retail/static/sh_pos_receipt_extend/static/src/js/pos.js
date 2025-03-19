odoo.define("sh_pos_receipt_extend.pos", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var core = require("web.core");
    var rpc = require("web.rpc");
    var Session = require("web.session");
    const Chrome = require("point_of_sale.Chrome");

    var qweb = core.qweb;
    var _t = core._t;

    const Registries = require("point_of_sale.Registries");
    const OrderReceipt = require("point_of_sale.OrderReceipt");

    const PosResOrderReceipt = (OrderReceipt) =>
        class extends OrderReceipt {
            constructor() {
                super(...arguments);
                var self = this;
                var order = this.env.pos.get_order();
                var order_barcode = order.uid.split("-");
                order.barcode = "";
                _.each(order_barcode, function (splited_barcode) {
                    order.barcode = order.barcode + splited_barcode;
                });
                var image_path = $("img.barcode_class").attr("src");
                $.ajax({
                    url: image_path,
                    type: "HEAD",
                    error: function () {
                        if (self.env.pos.get_order()) {
                            self.env.pos.get_order()["is_barcode_exit"] = false;
                        }
                    },
                    success: function () {
                        if (self.env.pos.get_order()) {
                            self.env.pos.get_order()["is_barcode_exit"] = true;
                        }
                    },
                });
                var image_path = $("img.qr_class").attr("src");
                $.ajax({
                    url: image_path,
                    type: "HEAD",
                    error: function () {
                        if (self.env.pos.get_order()) {
                            self.env.pos.get_order()["is_qr_exit"] = false;
                        }
                    },
                    success: function () {
                        if (self.env.pos.get_order()) {
                            self.env.pos.get_order()["is_qr_exit"] = true;
                        }
                    },
                });
                if (order.is_to_invoice() && self.env.pos.config.sh_pos_receipt_invoice) {
                    rpc.query({
                        model: "pos.order",
                        method: "search_read",
                        domain: [["pos_reference", "=", order["name"]]],
                        fields: ["account_move"],
                    }).then(function (orders) {
                        if (orders.length > 0 && orders[0]["account_move"] && orders[0]["account_move"][1]) {
                            var invoice_number = orders[0]["account_move"][1].split(" ")[0];
                            order["invoice_number"] = invoice_number;
                        }
                        self.render();
                    });
                }

                rpc.query({
                    model: 'pos.order',
                    method: 'search_read',
                    domain: [['pos_reference', '=', order.name]],
                    fields: ['name']
                }).then(function (callback) {
                    if (callback && callback.length > 0) {
                        order['pos_recept_name'] = callback[0]['name']
                    }
                    self.render();
                })
            }
            mounted() {

                var self = this;
//                if ($("#barcode") && $("#barcode").length > 0) {
//                    JsBarcode("#barcode")
//                        .options({ font: "OCR-B", displayValue: false }) // Will affect all barcodes
//                        .CODE128(self.env.pos.get_order().barcode, { fontSize: 18, textMargin: 0, height: 50 })
//                        .blank(0) // Create space between the barcodes
//                        .render();
//                }
                if ($("#barcode_receipt") && $("#barcode_receipt").length > 0) {
                    JsBarcode("#barcode_receipt")
                        .options({ font: "OCR-B", displayValue: false }) // Will affect all barcodes
                        .CODE128(self.env.pos.get_order().barcode, { fontSize: 18, textMargin: 0, height: 50 })
                        .render();
                }
                if ($('#qr_code') && $('#qr_code').length > 0) {
                    $('#qr_code').qrcode({ text: self.env.pos.get_order().barcode, width: 50, height: 50 });
                }
                //            	jquery('#qrcode').qrcode("this plugin is great");
                super.mounted()
            }
        };
    Registries.Component.extend(OrderReceipt, PosResOrderReceipt);
});
