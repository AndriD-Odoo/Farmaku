odoo.define("sh_pos_order_discount.pos", function (require) {
    var models = require("point_of_sale.models");
    const OrderWidget = require("point_of_sale.OrderWidget");
    const Registries = require("point_of_sale.Registries");

    const DiscountOrderWidget = (OrderWidget) =>
        class extends OrderWidget {
            constructor() {
                super(...arguments);
            }
            _updateSummary() {
                var order = this.order;
                var total_discount = 0;
                if (order) {
                    if (order.get_orderlines()) {
                        _.each(order.get_orderlines(), function (each_orderline) {
                            if (each_orderline.get_unit() != each_orderline.get_current_uom() ){
                                total_discount = total_discount + (each_orderline.update_unit_price * each_orderline.quantity - each_orderline.get_display_price());
                            }else{
                                total_discount = total_discount + (each_orderline.price * each_orderline.quantity - each_orderline.get_display_price());
                            }
                        });
                    }
                }
                if (total_discount) {
                    this.state.discount = total_discount;
                } else {
                    this.state.discount = 0.00;
                }
                super._updateSummary(...arguments);
            }
        };

    Registries.Component.extend(OrderWidget, DiscountOrderWidget);

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            this.global_discount;
            this.fix_discount;
            this.total_discount;
            _super_orderline.initialize.call(this, attr, options);
        },
        set_global_discount: function (discount) {
            this.global_discount = discount;
        },
        get_global_discount: function () {
            return this.global_discount;
        },
        set_fix_discount: function (discount) {
            this.fix_discount = discount;
        },
        get_fix_discount: function () {
            return this.fix_discount;
        },
        get_sh_discount_str: function () {
            return this.discount.toFixed(2);
        },
        set_total_discount: function (discount) {
            this.total_discount = discount;
        },
        get_total_discount: function () {
            return this.total_discount || false;
        },
        set_custom_discount: function (discount) {
            var disc = Math.min(Math.max(discount || 0, 0), 100);
            this.discount = disc;
            this.discountStr = '' + disc;
            this.trigger('change', this);
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attr, options) {
            this.order_global_discount;
            //    		this.order_total_discount;
            _super_order.initialize.call(this, attr, options);
        },
        set_order_global_discount: function (discount) {
            this.order_global_discount = discount;
        },
        get_order_global_discount: function () {
            return this.order_global_discount || false;
        },
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function () {
            var self = this;
            _super_posmodel.initialize.apply(this, arguments);
            this.is_global_discount = false;
        },
    });
});
