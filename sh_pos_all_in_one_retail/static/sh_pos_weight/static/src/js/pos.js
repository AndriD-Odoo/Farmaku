odoo.define('require', function (require) {
    'use strict';

    const { useState, useRef, onPatched } = owl.hooks;
    var models = require("point_of_sale.models");
    const OrderWidget = require("point_of_sale.OrderWidget");
    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");


    // models.load_fields('product.product', ['weight', 'volume'])

    const ShOrderWidget = (OrderWidget) =>
        class extends OrderWidget {
            constructor() {
                super(...arguments);
            }
            _updateSummary() {
                var order = this.env.pos.get_order()
                var self = this
                if (this.env.pos.config.enable_weight) {
                    self.total_weight = 0.0
                    if (order && order.orderlines) {
                        order.orderlines.each(function (line) {
                            self.total_weight += line.product.weight * line.quantity
                        })
                        order.total_weight = self.total_weight
                    } else {
                        self.total_weight = 0.0
                    }
                }
                if (this.env.pos.config.enable_volume) {
                    self.total_volume = 0.0
                    if (order && order.orderlines) {
                        order.orderlines.each(function (line) {
                            self.total_volume += line.product.volume * line.quantity
                        })
                        order.total_volume = self.total_volume
                    } else {
                        self.total_volume = 0.0
                    }
                }
                super._updateSummary(...arguments);
            }
        };

    Registries.Component.extend(OrderWidget, ShOrderWidget);

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            _super_order.initialize.apply(this, arguments);
            this.total_weight = 0
            this.total_volume = 0
        },
        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.apply(this, arguments);
            json.total_product_weight = this.total_weight || false
            json.total_product_volume = this.total_volume || false
            return json;
        },
    })

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            _super_orderline.initialize.call(this, attr, options)
        },
        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.apply(this, arguments);
            json.product_weight = this.product.weight
            json.product_volume = this.product.volume
            json.total_product_weight = this.product.weight * this.quantity || false
            json.total_product_volume = this.product.volume * this.quantity || false
            return json;
        },

        export_for_printing: function () {
            var receipt = _super_orderline.export_for_printing.apply(this, arguments);
            receipt['weight'] = this.product.weight * this.quantity
            receipt['volume'] = this.product.volume * this.quantity
            return receipt
        },
    })
});
