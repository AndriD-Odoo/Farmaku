odoo.define('sh_pos_order_lable.pos', function (require, factory) {
    'use strict';

    const PosComponent = require("point_of_sale.PosComponent");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    var DB = require("point_of_sale.DB");
    const OrderWidget = require("point_of_sale.OrderWidget");
    var core = require("web.core");
    var QWeb = core.qweb;

    var models = require("point_of_sale.models");

    DB.include({
        get_product_by_name(name) {

            var products = this.product_by_id

            var product1 = {}
            _.each(products, function (product) {
                if (product.default_code == name) {
                    product1 = product
                }

            })
            return product1
        },
    })

    const RoundingOrderWidget = (OrderWidget) =>
        class extends OrderWidget {
            constructor() {
                super(...arguments);
            }
            _updateSummary() {
                super._updateSummary(...arguments);
                var self = this
                if (this.env.pos.get_order()) {
                    _.each(this.env.pos.get_order().get_orderlines(), function (line) {
                        if (line.product.default_code == 'sh_pos_order_label_line') {
                            line.quantity = 0
                            line.quantityStr = '' + 0
                        }
                    })
                }
            }
            remove_label(e) {
                this.env.pos.get_order().remove_label(e)
            }
        };

    Registries.Component.extend(OrderWidget, RoundingOrderWidget);

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {

            this.add_section = '';
            this.ref_label = '';

            if (options && options.json && options.json.add_section) {
                this.add_section = options.json.add_section
            }

            _super_orderline.initialize.call(this, attr, options);
        },
        set_orderline_label: function (value) {
            this.add_section = value
        },
        get_orderline_label: function () {
            return this.add_section
        },
        set_ref_label: function (value) {
            this.ref_label = value
        },
        get_ref_label: function () {
            return this.ref_label
        },
        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.call(this);
            json.add_section = this.add_section || null;
            return json
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            _super_order.initialize.apply(this, arguments);
            this.line_labels = [];
            this.apply_discount = options.pos.config.sh_enable_customer_discount
        },
        set_line_label: function (line_label) {
            this.line_labels.push(line_label);
        },
        get_line_label: function () {
            return this.line_labels
        },
        remove_label(e) {
            var self = this
            var res;
            if ($(e.currentTarget).parent().data('label_id')) {
                res = self.get_label_line_by_name($(e.currentTarget).parent().data('label_id'))
            }
            if (this.pos.config.enabel_delete_label_with_product) {
                var remove = []
                _.each(this.get_orderlines(), function (orderline) {
                    if (orderline) {
                        if (orderline['ref_label'] && res.add_section == orderline['ref_label']) {
                            remove.push(orderline)
                        } else {
                            if (orderline.add_section == '' && orderline.product.default_code == "sh_pos_order_label_line") {
                                remove.push(orderline)
                            }
                        }
                    }
                })
                for (var i = 0; i < remove.length; i++) {
                    self.remove_orderline(remove[i])
                }
                self.remove_orderline(res)
            } else {
                self.remove_orderline(res)
            }

        },
        get_orderline_by_id(id) {
            var result = []
            _.each(this.get_orderlines(), function (line) {
                if (line.id == id) {
                    result.push(line)
                }
            })
            return result
        },
        get_label_line_by_name(name) {
            var lines = this.get_orderlines()
            var res = []
            _.each(lines, function (line) {
                if (line.add_section == name) {
                    res.push(line)
                }
            })
            return res[0]
        },
        add_product: function (product, options) {

            if (this.pos.config.enabel_delete_label_with_product) {
                if (this._printed) {
                    this.destroy();
                    return this.pos.get_order().add_product(product, options);
                }
                this.assert_editable();
                options = options || {};
                var line = new models.Orderline({}, { pos: this.pos, order: this, product: product });
                this.fix_tax_included_price(line);

                _.each(this.get_orderlines(), function (orderline) {
                    if (orderline.add_section) {
                        line.set_ref_label(orderline.add_section)
                    }
                })

                if (options.quantity !== undefined) {
                    line.set_quantity(options.quantity);
                }

                if (options.price_extra !== undefined) {
                    line.price_extra = options.price_extra;
                    line.set_unit_price(line.product.get_price(this.pricelist, line.get_quantity(), options.price_extra));
                    this.fix_tax_included_price(line);
                }

                if (options.price !== undefined) {
                    line.set_unit_price(options.price);
                    this.fix_tax_included_price(line);
                }

                if (options.lst_price !== undefined) {
                    line.set_lst_price(options.lst_price);
                }

                if (this.apply_discount) {
                    var client = this.get_client()
                    if (client) {
                        line.set_discount(client.sh_customer_discount)
                    }
                }
                if (options.discount !== undefined) {
                    line.set_discount(options.discount);
                }

                if (options.description !== undefined) {
                    line.description += options.description;
                }

                if (options.extras !== undefined) {
                    for (var prop in options.extras) {
                        line[prop] = options.extras[prop];
                    }
                }
                if (options.is_tip) {
                    this.is_tipped = true;
                    this.tip_amount = options.price;
                }

                var to_merge_orderline;
                for (var i = 0; i < this.orderlines.length; i++) {
                    if (this.orderlines.at(i).can_be_merged_with(line) && options.merge !== false) {
                        to_merge_orderline = this.orderlines.at(i);
                    }
                }
                if (to_merge_orderline) {
                    to_merge_orderline.merge(line);
                    this.select_orderline(to_merge_orderline);
                } else {
                    this.orderlines.add(line);
                    this.select_orderline(this.get_last_orderline());
                }

                if (options.draftPackLotLines) {
                    this.selected_orderline.setPackLotLines(options.draftPackLotLines);
                }
                if (this.pos.config.iface_customer_facing_display) {
                    this.pos.send_current_order_to_customer_facing_display();
                }
            } else {
                _super_order.add_product.call(this, product, options);
            }
            var order = this.pos.get_order();
            if (options !== undefined) {
                if (options.line_id) {
                    order.selected_orderline.set_line_id(options.line_id);
                    order.selected_orderline.set_old_line_id(options.old_line_id);
                }
            }
            if (this.pos.config.sh_enable_coupon && this.pos.db.cart_coupon && this.pos.db.cart_coupon.length > 0 && this.pos.get_order().get_client()) {
                this.apply_coupon();
            }
        }
    });

    class LabelPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.section = 'Section' || "";
        }
        confirm() {
            var self = this
            var value = $(document.getElementById('label_value')).val()
            if (value) {
                var order = this.env.pos.get_order()
                var line_label = new models.OrderLineLabel({
                    pos: self.env.pos,
                    order: order,
                    label: value
                });
                var product = this.env.pos.db.get_product_by_name('sh_pos_order_label_line')
                if (product) {
                    var line = new models.Orderline({}, { pos: self.env.pos, order: order, product: product })
                    line.set_orderline_label(value)
                    order.add_orderline(line);

                    order.set_line_label(line_label)

                    this.trigger('close-popup')
                }

            } else {
                alert('Please Enter Label!')
            }
        }
    }
    LabelPopup.template = 'LabelPopup'

    Registries.Component.add(LabelPopup)


    class AddLabelBtn extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click-add-button', this.onClickTemplateLoad)
        }
        onClickTemplateLoad() {
            this.showPopup("LabelPopup")
        }
    }

    AddLabelBtn.template = 'AddlabelButton';

    ProductScreen.addControlButton({
        component: AddLabelBtn,
        condition: function () {
            return this.env.pos.config.enable_order_line_label
        }
    })

    Registries.Component.add(AddLabelBtn)

    var label_id = 1;
    models.OrderLineLabel = Backbone.Model.extend({
        initialize: function (options) {
            this.pos = options.pos;
            this.order = options.order;
            this.line_id = options.line_id;
            this.label_id = label_id++;
            this.label = options.label;
        },
        set_label: function (label) {
            this.label = label;
        },
        get_label: function () {
            return this.label;
        }
    });

    return {
        AddLabelBtn,
        LabelPopup,
    }

});
