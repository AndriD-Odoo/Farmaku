odoo.define("sh_pos_secondary.screens", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var core = require("web.core");
    var rpc = require("web.rpc");
    var Session = require("web.session");
    var DB = require("point_of_sale.DB");
    var concurrency = require("web.concurrency");
    var utils = require("web.utils");
    var field_utils = require("web.field_utils");
    const ProductItem = require("point_of_sale.ProductItem");
    const Registries = require('point_of_sale.Registries');

    var QWeb = core.qweb;
    var _t = core._t;
    var Mutex = concurrency.Mutex;
    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;

    // models.load_fields("product.template", ["sh_secondary_uom"]);
    // models.load_fields("product.product", ["sh_secondary_uom", 'sh_is_secondary_unit']);
    models.load_fields("pos.order.line", ["secondary_qty"]);

    const shProductItem = (ProductItem) =>
        class extends ProductItem {
            get price() {
                var self = this
                var price_val = super.price
                var unit_price = this.props.product.get_price(this.pricelist, 1)
                if (this.props.product.sh_secondary_uom && this.props.product.sh_is_secondary_unit && this.env.pos.config.enable_price_to_display && this.env.pos.config.select_uom_type == 'secondary' && this.env.pos.config.sh_enable_seconadry) {
                    var secondary = self.get_product_secondary_unit()
                    var primary = self.get_product_unit()
                    var k = self.convert_product_qty_uom(1, primary, secondary)

                    this.props.product['temp_price'] = unit_price * k
                    return this.env.pos.format_currency(unit_price * k)
                } else {
                    return price_val
                }
            }
            convert_product_qty_uom(quantity, to_uom, from_uom) {
                var to_uom = to_uom;
                var from_uom = from_uom;
                var from_uom_factor = from_uom.factor;
                var amount = quantity / from_uom_factor;
                if (to_uom) {
                    var to_uom_factor = to_uom.factor;
                    amount = amount * to_uom_factor;
                }
                return amount;
            }
            get_product_secondary_unit() {
                var secondary_unit_id = this.props.product.sh_secondary_uom;
                if (!secondary_unit_id) {
                    return this.props.product.get_unit()
                }
                secondary_unit_id = secondary_unit_id[0];
                if (!this.env.pos) {
                    return undefined;
                }

                return this.env.pos.units_by_id[secondary_unit_id];
            }
            get_product_unit() {
                var unit_id = this.props.product.uom_id;
                if (!unit_id) {
                    return undefined;
                }
                unit_id = unit_id[0];
                if (!this.env.pos) {
                    return undefined;
                }
                return this.env.pos.units_by_id[unit_id];
            }
        }

    Registries.Component.extend(ProductItem, shProductItem)
    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        // when change pricelist
        set_pricelist: function (pricelist) {
            var self = this;
            this.pricelist = pricelist;
            var lines_to_recompute = _.filter(this.get_orderlines(), function (line) {
                return !line.price_manually_set;
            });
            _.each(lines_to_recompute, function (line) {
                var primary_uom = line.get_unit();
                var secondary_uom = line.get_secondary_unit();
                var current_uom = line.get_current_uom() || primary_uom;
                if (current_uom == primary_uom) {
                    line.set_unit_price(line.product.get_price(self.pricelist, line.get_quantity()));
                    self.fix_tax_included_price(line);
                } else {
                    line.set_unit_price(line.product.get_price(self.pricelist, line.get_primary_quantity()));
                    self.fix_tax_included_price(line);
                }
            });
            this.trigger("change");
        },
    });
    // 
    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attributes, options) {
            _super_orderline.initialize.call(this, attributes, options);
            this.is_secondary = false
//            debugger;
            if (this.order.return_order){
                this.set_current_uom(this.get_unit())
            };
            if (options.price) {
                this.set_unit_price(options.price);
            } else {
                var primary_uom = this.get_unit();
                var secondary_uom = this.get_secondary_unit();
                var current_uom = this.get_current_uom() || primary_uom;
                // Initialization of price unit
                if (current_uom == primary_uom) {
                    //                    this.set_unit_price(this.product.get_price(this.order.pricelist, 12));
                } else {
                    this.set_unit_price(this.product.get_price(this.order.pricelist, this.get_primary_quantity()));
                }
            }
        },

        // return the unit of measure of the product
        get_unit: function () {
            var unit_id = this.product.uom_id;
            if (!unit_id) {
                return undefined;
            }
            unit_id = unit_id[0];
            if (!this.pos) {
                return undefined;
            }
            return this.pos.units_by_id[unit_id];
        },
        get_secondary_unit: function () {
            var secondary_unit_id = this.product.sh_secondary_uom;
            if (!secondary_unit_id) {
                return this.get_unit();
            }
            secondary_unit_id = secondary_unit_id[0];
            if (!this.pos) {
                return undefined;
            }

            return this.pos.units_by_id[secondary_unit_id];
        },
        get_display_product_unit_price() {
            var self = this;
            var value = 0;
            var secondary = self.get_secondary_unit()
            var primary = self.get_unit()

            var k = self.convert_qty_uom(1, primary, secondary)

            value = this.product.get_price(this.order.pricelist, this.get_quantity()) * k
            this.update_unit_price = value;
            return this.pos.format_currency(value)
        },
        set_quantity: function (quantity, keep_price) {
//            debugger;
            this.order.assert_editable();
            _super_orderline.set_quantity.apply(this, arguments);
            var self = this
            var primary_uom = this.get_unit();
            if (this.pos.config.sh_enable_seconadry && this.pos.config.select_uom_type != 'secondary') {
                var secondary_uom = primary_uom;
                if (this.order.orderlines.models.includes(this)) {
                    this.is_secondary = true
                    secondary_uom = this.get_secondary_unit();
                }
            } else {
                this.is_secondary = true
                var secondary_uom = this.get_secondary_unit();
            }
            if (this.get_current_uom() == undefined) {
                this.set_current_uom(secondary_uom);
            }
            // // Initialization of qty when product added
            var current_uom = this.get_current_uom() || primary_uom;
            if (current_uom == primary_uom) {
                this.set_current_uom(primary_uom);
                this.set_primary_quantity(this.get_quantity());

                var converted_qty = this.convert_qty_uom(this.quantity, secondary_uom, current_uom);
                this.set_secondary_quantity(converted_qty);
                // just like in sale.order changing the quantity will recompute the unit price
                if (!keep_price && !this.price_manually_set) {
                    this.set_unit_price(this.product.get_price(this.order.pricelist, this.get_quantity()));
                    this.order.fix_tax_included_price(this);
                }
            } else {
                var converted_qty = this.convert_qty_uom(this.quantity, primary_uom, current_uom);
                this.set_primary_quantity(converted_qty);
                this.set_secondary_quantity(this.get_quantity());
                this.set_current_uom(secondary_uom);
                if (!keep_price && !this.price_manually_set) {
                    this.set_unit_price(this.product.get_price(this.order.pricelist, converted_qty));
                    this.order.fix_tax_included_price(this);
                }
            }
            this.trigger("change", this);
        },

        convert_qty_uom: function (quantity, to_uom, from_uom) {
            var to_uom = to_uom;
            var from_uom = from_uom;
            var from_uom_factor = from_uom.factor;
            var amount = quantity / from_uom_factor;
            if (to_uom) {
                var to_uom_factor = to_uom.factor;
                amount = amount * to_uom_factor;
            }
            return amount;
        },
        // return the quantity of product
        set_secondary_quantity: function (secondary_quantity, keep_price) {
            this.order.assert_editable();
            var quant = parseFloat(secondary_quantity) || 0;
            this.secondary_quantity = quant;
        },
        set_primary_quantity: function (primary_quantity, keep_price) {
            this.order.assert_editable();
            var quant = parseFloat(primary_quantity) || 0;
            this.primary_quantity = quant;
        },
        get_secondary_quantity: function () {
            return this.secondary_quantity;
        },

        get_primary_quantity: function () {
            return this.primary_quantity;
        },

        set_current_uom: function (uom_id) {
            this.order.assert_editable();
            this.current_uom = uom_id;
            this.trigger("change", this);
        },
        change_current_uom: function (uom_id) {
            this.order.assert_editable();
            this.current_uom = uom_id;
            if (this.current_uom == this.get_unit()) {
                this.set_quantity(this.get_primary_quantity());
            } else {
                this.set_quantity(this.get_secondary_quantity());
            }
            this.trigger("change", this);
        },
        get_current_uom: function () {
            return this.current_uom;
        },
        get_base_price: function () {
            var rounding = this.pos.currency.rounding;
            var primary_uom = this.get_unit();
            var secondary_uom = this.get_secondary_unit();
            var current_uom = this.get_current_uom() || primary_uom;
            // computation of base price
            if (current_uom == primary_uom) {
                return round_pr(this.get_unit_price() * this.get_quantity() * (1 - this.get_discount() / 100), rounding);
            } else {
                return round_pr(this.get_unit_price() * this.get_primary_quantity() * (1 - this.get_discount() / 100), rounding);
            }
        },
        get_all_prices: function () {
            var self = this;

            var price_unit = this.get_unit_price() * (1.0 - this.get_discount() / 100.0);
            var taxtotal = 0;

            var product = this.get_product();
            var taxes_ids = product.taxes_id;
            var taxes = this.pos.taxes;
            var taxdetail = {};
            var product_taxes = [];

            _(taxes_ids).each(function (el) {
                var tax = _.detect(taxes, function (t) {
                    return t.id === el;
                });
                product_taxes.push.apply(product_taxes, self._map_tax_fiscal_position(tax));
            });

            var primary_uom = this.get_unit();
            var secondary_uom = this.get_secondary_unit();
            var current_uom = this.get_current_uom() || primary_uom;
            // computation of all price and tax
            if (current_uom == primary_uom) {
                var all_taxes = this.compute_all(product_taxes, price_unit, this.get_quantity(), this.pos.currency.rounding);
                var all_taxes_before_discount = this.compute_all(product_taxes, this.get_unit_price(), this.get_quantity(), this.pos.currency.rounding);
            } else {
                var all_taxes = this.compute_all(product_taxes, price_unit, this.get_primary_quantity(), this.pos.currency.rounding);
                var all_taxes_before_discount = this.compute_all(product_taxes, this.get_unit_price(), this.get_primary_quantity(), this.pos.currency.rounding);
            }

            _(all_taxes.taxes).each(function (tax) {
                taxtotal += tax.amount;
                taxdetail[tax.id] = tax.amount;
            });

            return {
                priceWithTax: all_taxes.total_included,
                priceWithoutTax: all_taxes.total_excluded,
                priceSumTaxVoid: all_taxes.total_void,
                priceWithTaxBeforeDiscount: all_taxes_before_discount.total_included,
                tax: taxtotal,
                taxDetails: taxdetail,
            };
        },
        export_as_JSON: function () {
            var vals = _super_orderline.export_as_JSON.apply(this, arguments);
            vals["qty"] = this.get_primary_quantity();
            vals["secondary_qty"] = this.get_secondary_quantity();
            if (this.is_secondary) {
                vals["secondary_uom_id"] = this.get_secondary_unit().id;
            }
            return vals;
        },
        export_for_printing: function () {
            var res = _super_orderline.export_for_printing.apply(this, arguments);
            if (this.pos.config.enable_price_to_display && this.pos.config.sh_enable_seconadry) {
                if (this.product.sh_secondary_uom && this.get_current_uom().id == this.product.sh_secondary_uom[0]) {
                    res['unit_price'] = this.update_unit_price
                } else {
                    res['unit_price'] = this.get_unit_display_price()
                }
            } else {
                res['unit_price'] = this.get_unit_display_price()
            } 
            res['secondary_unit_name'] = this.get_current_uom().name;
            if (this.product && this.product.uom_id && this.product.uom_id[1]) {
                res['primary_unit_name'] = this.product.uom_id[1];
            }
            return res
        },
    });
});
odoo.define("sh_pos_secondary.ChangeUOMButton", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const Chrome = require("point_of_sale.Chrome");
    const { Gui } = require("point_of_sale.Gui");

    class ChangeUOMButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("chanege-product-uom", this.onClickUOM);
        }
        async onClickUOM() {
            var selectionList = [];
            if (this.env.pos.get_order()) {
                var line = this.env.pos.get_order().get_selected_orderline();
            }
            if (line) {
                var uom = line.get_unit();
                if (uom) {
                    selectionList.push({ id: uom.id, isSelected: true, label: uom.display_name, item: uom });
                    var secondary_uom = line.get_secondary_unit();
                    if (secondary_uom != uom) {
                        selectionList.push({ id: secondary_uom.id, isSelected: false, label: secondary_uom.display_name, item: secondary_uom });
                    }
                }
            }

            _.each(selectionList, function (each_uom) {
                if (each_uom.label === line.get_current_uom().name) {
                    each_uom.isSelected = true;
                } else {
                    each_uom.isSelected = false;
                }
            });
            const { confirmed, payload: selectedUOM } = await this.showPopup("SelectionPopup", {
                title: this.env._t("Select the UOM"),
                list: selectionList,
            });

            if (confirmed) {
                line.change_current_uom(selectedUOM);
            }
        }
    }
    ChangeUOMButton.template = "ChangeUOMButton";

    ProductScreen.addControlButton({
        component: ChangeUOMButton,
        condition: function () {
            return this.env.pos.config.sh_enable_seconadry;
        },
    });

    Registries.Component.add(ChangeUOMButton);

    return ChangeUOMButton;
});
