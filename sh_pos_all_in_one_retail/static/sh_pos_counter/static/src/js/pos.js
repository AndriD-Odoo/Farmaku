odoo.define("sh_pos_counter.pos", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var core = require("web.core");
    var QWeb = core.qweb;
    var _t = core._t;
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
                const total_items = this.order ? this.order.get_total_items() : 0;
                this.state.total_items = total_items;
                const total_qty = this.order ? this.order.get_total_qty() : 0;
                // total_qty = parseFloat
                this.state.total_qty = total_qty.toFixed(2);
                super._updateSummary(...arguments);
            }
        };

    Registries.Component.extend(OrderWidget, RoundingOrderWidget);

    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        get_total_items: function () {
            var order = this.pos.get_order();
            var sum = 0;
            if (order) {
                var lines = _.filter(order.get_orderlines(), function (line) {
                    if(!line.product.available_in_pos){
                        return false
                    } else{
                        return true
                    }
                })
                
                sum = lines.length
            }
            return sum;
        },
        get_total_qty: function () {

            var order = this.pos.get_order();
            var sum = 0;
            if (order) {
                var lines = _.filter(order.get_orderlines(), function (line) {
                    if(!line.product.available_in_pos){
                        return false
                    } else{
                        return true
                    }
                })
                lines.forEach(function (orderline) {
                    if (orderline.get_quantity()) {

                        sum += orderline.get_quantity();
                    }
                });
            }
            return sum;
        },
        export_for_printing: function () {
            var receipt = _super_Order.export_for_printing.apply(this, arguments);
            var order = this.pos.get_order();
            var self = this
            var sum = 0;
            _.each(order.get_orderlines(), function (each_orderline) {
                if (each_orderline.product.id != self.pos.config.round_product_id[0]) {
                    sum = sum + 1
                }
            });
            var qty = 0;
            _.each(order.get_orderlines(), function (each_orderline) {
                if (each_orderline.product.id != self.pos.config.round_product_id[0]) {
                    qty = qty + each_orderline.get_quantity()
                }
            });
            receipt["total_items"] = sum;
            receipt["total_qty"] = qty
            return receipt;
        },
        getOrderReceiptEnv: function () {
            var res = _super_Order.getOrderReceiptEnv.apply(this, arguments);

            res['total_items'] = 7
            res['total_qty'] = this.get_total_qty()
            return res;
        },
        export_as_JSON: function () {
            var json = _super_Order.export_as_JSON.apply(this, arguments);
            json.total_item = this.get_total_items() || null;
            json.total_qty = this.get_total_qty() || null;
            return json;
        },
    });

    return OrderWidget;
});
