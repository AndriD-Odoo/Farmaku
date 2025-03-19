odoo.define("sh_pos_wh_stock_adv.pos", function (require) {
    "use strict";

    const Chrome = require("point_of_sale.Chrome");
    const Registries = require("point_of_sale.Registries");
    var bus_service = require("bus.BusService");
    const bus = require("bus.Longpolling");
    const session = require("web.session");
    var rpc = require("web.rpc");
    var core = require("web.core");
    const PaymentScreen = require("point_of_sale.PaymentScreen");
    var DB = require("point_of_sale.DB");
    var models = require("point_of_sale.models");

    var _t = core._t;

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({

    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            _super_posmodel.initialize.call(this, session, attributes);
            this.is_pos_order = false;
            this.is_refund_button_click = false;
        },
    });

    const PosWHAdvPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            async _finalizeValidation() {
                this.env.pos.is_pos_order = true;
                await super._finalizeValidation();
                this.env.pos.is_pos_order = false;
            }
        };
    Registries.Component.extend(PaymentScreen, PosWHAdvPaymentScreen);

    const PosResChrome = (Chrome) =>
        class extends Chrome {
            _buildChrome() {
                super._buildChrome();
                var bus_service_obj = bus_service.prototype;
                bus_service_obj["env"] = this.env;
                bus_service_obj.call("bus_service", "updateOption", "stock.update", session.uid);
                bus_service_obj.call("bus_service", "onNotification", this, this._onNotification);
                bus_service_obj.call("bus_service", "startPolling");
            }
            
            _onNotification(notifications) {
                var self = this;
                if (self && self.env && self.env.pos && self.env.pos.config && self.env.pos.config.sh_display_stock && self.env.pos.config.sh_update_real_time_qty && !self.env.pos.is_pos_order) {
                    if (notifications) {
                        _.each(notifications, function (each_notification) {
                            if (each_notification && each_notification[1] && each_notification[1]["stock_update"]) {
                                if (each_notification[1]["stock_update"][0]["product_id"] && each_notification[1]["stock_update"][0]["location_id"] && each_notification[1]["stock_update"][0]["quantity"]) {
                                    if (
                                        self &&
                                        self.env &&
                                        self.env.pos &&
                                        self.env.pos.db &&
                                        self.env.pos.db.quant_by_product_id &&
                                        self.env.pos.db.quant_by_product_id[each_notification[1]["stock_update"][0]["product_id"][0]] &&
                                        self.env.pos.db.quant_by_product_id[each_notification[1]["stock_update"][0]["product_id"][0]][each_notification[1]["stock_update"][0]["location_id"][0]]
                                    ) {
                                        if (each_notification[1]["stock_update"][0]["location_id"] && each_notification[1]["stock_update"][0]["location_id"][0] == self.env.pos.config.sh_pos_location[0]) {
                                            self.env.pos.db.quant_by_product_id[each_notification[1]["stock_update"][0]["product_id"][0]][each_notification[1]["stock_update"][0]["location_id"][0]] =
                                                each_notification[1]["stock_update"][0]["quantity"];
                                            if (
                                                $(document.querySelectorAll('[data-product-id="' + each_notification[1]["stock_update"][0]["product_id"][0] + '"]')) &&
                                                $(document.querySelectorAll('[data-product-id="' + each_notification[1]["stock_update"][0]["product_id"][0] + '"]'))[0]
                                            ) {
                                                if ($(document.querySelectorAll('[data-product-id="' + each_notification[1]["stock_update"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("price-tag")) {
                                                    $($(document.querySelectorAll('[data-product-id="' + each_notification[1]["stock_update"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("sh_warehouse_display")).text(
                                                        each_notification[1]["stock_update"][0]["quantity"]
                                                    );
                                                }
                                            }
                                        }
                                    } else {
                                        if (!self.env.pos.db.quant_by_product_id[each_notification[1]["stock_update"][0]["product_id"][0]]) {
                                            self.env.pos.db.quant_by_product_id[each_notification[1]["stock_update"][0]["product_id"][0]] = {};
                                            self.env.pos.db.quant_by_product_id[each_notification[1]["stock_update"][0]["product_id"][0]][each_notification[1]["stock_update"][0]["location_id"][0]] =
                                                each_notification[1]["stock_update"][0]["quantity"];
                                            if (each_notification[1]["stock_update"][0]["product_id"] && each_notification[1]["stock_update"][0]["product_id"][0]) {
                                                if (
                                                    $(document.querySelectorAll('[data-product-id="' + each_notification[1]["stock_update"][0]["product_id"][0] + '"]')) &&
                                                    $(document.querySelectorAll('[data-product-id="' + each_notification[1]["stock_update"][0]["product_id"][0] + '"]'))[0]
                                                ) {
                                                    if (
                                                        $(document.querySelectorAll('[data-product-id="' + each_notification[1]["stock_update"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("price-tag") &&
                                                        $($(document.querySelectorAll('[data-product-id="' + each_notification[1]["stock_update"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("price-tag"))
                                                    ) {
                                                        $($(document.querySelectorAll('[data-product-id="' + each_notification[1]["stock_update"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("sh_warehouse_display")).text(
                                                            each_notification[1]["stock_update"][0]["quantity"]
                                                        );
                                                    }
                                                }
                                            }
                                        } else if (
                                            self.env.pos.db.quant_by_product_id[each_notification[1]["stock_update"][0]["product_id"][0]] &&
                                            !self.env.pos.db.quant_by_product_id[each_notification[1]["stock_update"][0]["product_id"][0]][each_notification[1]["stock_update"][0]["location_id"][0]]
                                        ) {
                                            self.env.pos.db.quant_by_product_id[each_notification[1]["stock_update"][0]["product_id"][0]][each_notification[1]["stock_update"][0]["location_id"][0]] =
                                                each_notification[1]["stock_update"][0]["quantity"];
                                            if (each_notification[1]["stock_update"][0]["product_id"] && each_notification[1]["stock_update"][0]["product_id"][0]) {
                                                if (
                                                    $(document.querySelectorAll('[data-product-id="' + each_notification[1]["stock_update"][0]["product_id"][0] + '"]')) &&
                                                    $(document.querySelectorAll('[data-product-id="' + each_notification[1]["stock_update"][0]["product_id"][0] + '"]'))[0]
                                                ) {
                                                    if (
                                                        $(document.querySelectorAll('[data-product-id="' + each_notification[1]["stock_update"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("price-tag") &&
                                                        $($(document.querySelectorAll('[data-product-id="' + each_notification[1]["stock_update"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("price-tag"))
                                                    ) {
                                                        $($(document.querySelectorAll('[data-product-id="' + each_notification[1]["stock_update"][0]["product_id"][0] + '"]'))[0].getElementsByClassName("sh_warehouse_display")).text(
                                                            each_notification[1]["stock_update"][0]["quantity"]
                                                        );
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        });
                    }
                }
            }
        };

    Registries.Component.extend(Chrome, PosResChrome);    

    return Chrome;
});
