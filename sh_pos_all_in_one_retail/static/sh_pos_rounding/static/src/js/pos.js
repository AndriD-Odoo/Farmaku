odoo.define("sh_pos_rounding.PaymentScreenStatus", function (require) {
    "use strict";
    const PaymentScreenStatus = require("point_of_sale.PaymentScreenStatus");
    const Registries = require("point_of_sale.Registries");
    const { useBarcodeReader } = require("point_of_sale.custom_hooks");
    const { useListener } = require("web.custom_hooks");

    const RoundingPaymentScreenStatus = (PaymentScreenStatus) =>
        class extends PaymentScreenStatus {
            constructor() {
                super(...arguments);
            }
            get totalDueText() {
                if (this.env.pos.config.sh_enable_rounding && this.currentOrder.get_is_payment_round() == true) {
                    return this.env.pos.format_currency(this.currentOrder.get_rounding_total(this.currentOrder.get_total_with_tax()));
                } else {
                    return this.env.pos.format_currency(this.currentOrder.get_total_with_tax() + this.currentOrder.get_rounding_applied());
                }
            }
        };

    Registries.Component.extend(PaymentScreenStatus, RoundingPaymentScreenStatus);

    return PaymentScreenStatus;
});
odoo.define("sh_pos_rounding.PaymentScreen", function (require) {
    "use strict";
    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");
    const { useBarcodeReader } = require("point_of_sale.custom_hooks");
    const { useListener } = require("web.custom_hooks");

    const RoundingPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
            }
            mounted() {
                if (this.env.pos.config.sh_enable_rounding) {
                    var order = this.env.pos.get_order();
                    $(this.el).find("#cb4").prop("checked", true);
                    order.set_is_payment_round(true);
                    var self = this;

                    // if toggle switch
                    $(this.el)
                        .find("#cb4")
                        .click(function () {
                            if ($(self.el).find("#cb4").prop("checked") == true) {
                                order.set_is_payment_round(true);
                                if (self.el.querySelector(".total")) {
                                    self.el.querySelector(".total").textContent = self.env.pos.format_currency(order.get_round_total_with_tax());
                                }
                            } else {
                                if (self.el.querySelector(".total")) {
                                    self.el.querySelector(".total").textContent = self.env.pos.format_currency(order.get_total_with_tax());
                                }
                                order.set_is_payment_round(false);
                            }
                        });
                }
            }
            async validateOrder(isForceValidate) {
                var order = this.currentOrder;
                if (order.get_is_payment_round()) {
                    var rounding_price = order.get_round_total_with_tax() - order.get_total_with_tax();
                    order.set_rounding_price(rounding_price);
                    var round_product = this.env.pos.db.get_product_by_id(this.env.pos.config.round_product_id[0]);
                    order.add_product(round_product, { quantity: 1, price: rounding_price });
                }
                super.validateOrder(isForceValidate)
            }
            addNewPaymentLine({ detail: paymentMethod }) {
                super.addNewPaymentLine(...arguments);
                $(this.el).find(".cb4_label").css("display", "none");
                $(this.el).find(".rounding_label").css("display", "none");
            }
        };

    Registries.Component.extend(PaymentScreen, RoundingPaymentScreen);

    return PaymentScreen;
});

odoo.define("sh_pos_rounding.OrderWidget", function (require) {
    "use strict";
    const OrderWidget = require("point_of_sale.OrderWidget");
    const Registries = require("point_of_sale.Registries");
    const { useBarcodeReader } = require("point_of_sale.custom_hooks");
    const { useListener } = require("web.custom_hooks");


    const RoundingOrderWidget = (OrderWidget) =>
        class extends OrderWidget {
            constructor() {
                super(...arguments);
            }
            _updateSummary() {
                if (this.order) {
                    if (this.env.pos.config.sh_enable_rounding) {
                        const total = this.order ? this.order.get_rounding_total(this.order.get_total_with_tax()) : 0;
                        const tax = this.order ? this.order.get_total_with_tax() - this.order.get_total_without_tax() : 0;
                        const rounding = this.order.get_rounding_total(this.order.get_total_with_tax()) - this.order.get_total_with_tax();

                        this.state.total = this.env.pos.format_currency(total);
                        this.state.rounding = this.env.pos.format_currency(rounding);
                        this.state.tax = this.env.pos.format_currency(tax);
                    } else {
                        const total = this.order ? this.order.get_total_with_tax() : 0;
                        const tax = this.order ? total - this.order.get_total_without_tax() : 0;
                        this.state.total = this.env.pos.format_currency(total);
                        this.state.tax = this.env.pos.format_currency(tax);
                    }
                }
                this.render();
            }
        };

    Registries.Component.extend(OrderWidget, RoundingOrderWidget);

    return OrderWidget;
});

odoo.define("sh_pos_rounding.screens", function (require) {
    "use strict";

    var core = require("web.core");
    var rpc = require("web.rpc");
    var models = require("point_of_sale.models");
    var DB = require("point_of_sale.DB");

    var utils = require("web.utils");
    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;
    var QWeb = core.qweb;
    var _t = core._t;

    // models.load_fields("product.template", ["is_rounding_product"]);
    // models.load_fields("product.product", ["is_rounding_product"]);

    var _super_Orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        get_discount: function(){
            if(this.product.is_rounding_product){
                return 0
            }else{
                return this.discount;
            }
        },
    })

    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_for_printing: function () {
            var orderlines = [];
            var self = this;
            var receipt = _super_Order.export_for_printing.apply(this, arguments);
            var round_product = this.pos.config.round_product_id[0];

            this.orderlines.each(function (orderline) {
                if (orderline.get_product().id != round_product) {
                    orderlines.push(orderline.export_for_printing());
                }
            });
            var order = this.pos.get_order();
            receipt["rounding_amount"] = order.get_rounding_amount();
            receipt["orderlines"] = orderlines;
            return receipt;
        },
        get_subtotal: function () {
            var round_product = this.pos.config.round_product_id[0];
            return round_pr(
                this.orderlines.reduce(function (sum, orderLine) {
                    if (orderLine.get_product().id != round_product) {
                        return sum + orderLine.get_display_price();
                    } else {
                        return sum;
                    }
                }, 0),
                this.pos.currency.rounding
            );
        },
        get_is_payment_round: function () {
            return this.is_payment_round;
        },
        set_is_payment_round: function (is_payment_round) {
            this.is_payment_round = is_payment_round;
            this.trigger("change", this);
        },
        get_round_total_with_tax: function () {
            return this.get_rounding_total(this.get_total_without_tax() + this.get_total_tax());
        },
        get_total_without_tax_report: function () {
            if (this.get_is_payment_round()) {
                return round_pr(
                    this.orderlines.reduce(function (sum, orderLine) {
                        if (orderLine.product.is_rounding_product) {
                            return sum;
                        } else {
                            return sum + orderLine.get_price_without_tax();
                        }
                    }, 0),
                    this.pos.currency.rounding
                );
            } else {
                return round_pr(
                    this.orderlines.reduce(function (sum, orderLine) {
                        return sum + orderLine.get_price_without_tax();
                    }, 0),
                    this.pos.currency.rounding
                );
            }
        },
        get_due: function (paymentline) {
            if (this.get_is_payment_round()) {
                if (!paymentline) {
                    var due = this.get_rounding_total(this.get_total_with_tax()) - this.get_total_paid();
                } else {
                    var due = this.get_rounding_total(this.get_total_with_tax());
                    var lines = this.paymentlines.models;
                    for (var i = 0; i < lines.length; i++) {
                        if (lines[i] === paymentline) {
                            break;
                        } else {
                            due -= lines[i].get_amount();
                        }
                    }
                }
            } else {
                if (!paymentline) {
                    var due = this.get_total_with_tax() - this.get_total_paid();
                } else {
                    var due = this.get_total_with_tax();
                    var lines = this.paymentlines.models;
                    for (var i = 0; i < lines.length; i++) {
                        if (lines[i] === paymentline) {
                            break;
                        } else {
                            due -= lines[i].get_amount();
                        }
                    }
                }
            }

            return round_pr(due, this.pos.currency.rounding);
        },
        get_change: function (paymentline) {
            if (this.get_is_payment_round()) {
                if (!paymentline) {
                    var change = this.get_total_paid() - this.get_rounding_total(this.get_total_with_tax());
                } else {
                    var change = -this.get_rounding_total(this.get_total_with_tax());
                    var lines = this.paymentlines.models;
                    for (var i = 0; i < lines.length; i++) {
                        change += lines[i].get_amount();
                        if (lines[i] === paymentline) {
                            break;
                        }
                    }
                }
            } else {
                if (!paymentline) {
                    var change = this.get_total_paid() - this.get_total_with_tax();
                } else {
                    var change = -this.get_total_with_tax();
                    var lines = this.paymentlines.models;
                    for (var i = 0; i < lines.length; i++) {
                        change += lines[i].get_amount();
                        if (lines[i] === paymentline) {
                            break;
                        }
                    }
                }
            }

            return round_pr(Math.max(0, change), this.pos.currency.rounding);
        },

        get_rounding_total: function (order_total) {
            var total_with_tax = order_total;
            var round_total = total_with_tax;
            if (this.pos.config.rounding_type == "fifty") {
                var division_by_50 = total_with_tax / 50;
                var floor_value = Math.floor(division_by_50);
                var ceil_value = Math.ceil(division_by_50);
                if (floor_value % 2 != 0) {
                    round_total = floor_value * 50;
                }
                if (ceil_value % 2 != 0) {
                    round_total = ceil_value * 50;
                }
            } else {
                round_total = Math.round(total_with_tax);
            }

            return round_total;
        },
        get_pos_orderlines: function (order_total) {
            if (this.get_is_payment_round()) {
                var orderlines = this.orderlines.models;
                var pos_orderlines = [];
                for (var i = 0; i < orderlines.length; i++) {
                    if (!orderlines[i].product.is_rounding_product) {
                        pos_orderlines.push(orderlines[i]);
                    }
                }
                return pos_orderlines;
            } else {
                return this.orderlines.models;
            }
        },
        get_rounding_amount: function () {
            return this.rounding_price;
        },
        set_rounding_price: function (price) {
            this.rounding_price = price;
        },
        getOrderReceiptEnv: function () {
            // Formerly get_receipt_render_env defined in ScreenWidget.
            var orderlines_list = [];
            var round_product = this.pos.config.round_product_id[0];

            var orderlines = this.get_orderlines() || false;
            _.each(orderlines, function (line) {
                if (line.get_product().id != round_product) {
                    orderlines_list.push(line);
                }
            });

            return {
                order: this,
                receipt: this.export_for_printing(),
                orderlines: orderlines_list,
                paymentlines: this.get_paymentlines(),
                rounding_amount: this.get_rounding_amount(),
            };
        },
    });
});
