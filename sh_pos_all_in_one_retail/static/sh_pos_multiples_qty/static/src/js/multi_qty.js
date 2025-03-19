odoo.define('sh_pos_multiples_qty.multi_qty', function (require) {
    'use strict';

    var models = require("point_of_sale.models");
    var utils = require("web.utils");
    var round_pr = utils.round_precision;
    var field_utils = require('web.field_utils');
    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");
    const { Gui } = require("point_of_sale.Gui");


    // models.load_fields("product.product", ["sh_multiples_of_qty"]);

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        set_quantity: function (quantity, keep_price) {
//            debugger;
            // if(!quantity){
            //     quantity = this.quantity
            // }
            var self = this;
            var old_qty = 0
            if(this.quantity && quantity && this.quantity > quantity){
                old_qty = 1
            }
            if (self.pos.get_order() && !self.pos.is_refund_button_click && !self.pos.get_order().is_refund_order) {
            	
                if (this.pos.config.sh_update_quantity_cart_change && this.quantity) {
                    if (this && this.pos.db && this.pos.db.quant_by_product_id && this.product && this.product.id && this.pos.db.quant_by_product_id[this.product.id]) {
                        this.pos.db.quant_by_product_id[this.product.id][this.pos.config.sh_pos_location[0]] = parseInt(this.pos.db.quant_by_product_id[this.product.id][this.pos.config.sh_pos_location[0]]) + this.quantity;
                    }
                }
            }
            this.order.assert_editable();
            var quant_by_product_id = this.pos.db.quant_by_product_id[this.product.id];
            var qty_available = quant_by_product_id ? quant_by_product_id[this.pos.config.sh_pos_location[0]] : 0;
            if (quantity === 'remove') {
                this.order.remove_orderline(this);
                return;
            } else {
                var quant = typeof (quantity) === 'number' ? quantity : (field_utils.parse.float('' + quantity) || 0);
                var unit = this.get_unit();
                if (unit) {
                    if (unit.rounding) {
                        var decimals = this.pos.dp['Product Unit of Measure'];
                        var rounding = Math.max(unit.rounding, Math.pow(10, -decimals));
                        if (this.pos.config.sh_multi_qty_enable) {
                            var qty = parseInt(this.product.sh_multiples_of_qty)
                            if (qty) {
                                if (qty <= quant) {
                                    if (quant / qty == parseInt(quant / qty)) {
                                        var loop = quant / qty
                                    } else {
                                        var loop = quant / qty + 1
                                    }
                                    for (var i = 2; i <= loop; i++) {
                                        var val = qty * i
                                        quant = val
                                    }
                                }
                                else {
                                    quant = qty
                                }
                            }
                        }
                        if (round_pr(quant, rounding) && this.pos.config.sh_show_qty_location && this.product.type == "product" && !this.product["is_added"]) {
                            if (qty_available - round_pr(quant, rounding) >= this.pos.config.sh_min_qty) {
                                this.quantity = round_pr(quant, rounding);
                                this.quantityStr = field_utils.format.float(this.quantity, { digits: [69, decimals] });
                            } else {
                                this.quantity = round_pr(0, rounding);
                                this.quantityStr = round_pr(0, rounding);
                                Gui.showPopup("QuantityWarningPopup", {
                                    product: this.product,
                                    quantity: round_pr(quant, rounding),
                                    product_image: this.get_image_url(this.product.id),
                                });
                            }
                        } else {
                            this.quantity = round_pr(quant, rounding);
                            this.quantityStr = field_utils.format.float(this.quantity, { digits: [69, decimals] });
                            this.product["is_added"] = false;
                        }
                    } else {

                        if (round_pr(quant, rounding) && this.pos.config.sh_show_qty_location && this.product.type == "product" && !this.product["is_added"]) {
                            if (qty_available - round_pr(quant, rounding) >= this.pos.config.sh_min_qty) {
                                this.quantity = round_pr(quant, 1);
                                this.quantityStr = this.quantity.toFixed(0);
                            } else {
                                this.quantity = round_pr(0, 1);    
                                this.quantityStr = round_pr(0, 1);
                                Gui.showPopup("QuantityWarningPopup", {
                                    product: this.product,
                                    quantity: round_pr(quant, 1),
                                    product_image: this.get_image_url(this.product.id),
                                });
                            }
                        } else {
                            this.quantity = round_pr(quant, 1);
                            this.quantityStr = this.quantity.toFixed(0);
                            this.product["is_added"] = false;
                        }
                    }
                } else {

                    if (round_pr(quant, rounding) && this.pos.config.sh_show_qty_location && this.product.type == "product" && !this.product["is_added"]) {
                        if (qty_available - round_pr(quant, rounding) >= this.pos.config.sh_min_qty) {
                            this.quantity = quant;
                            this.quantityStr = "" + this.quantity;
                        } else {
                            this.quantity = 0;
                            this.quantityStr = '0';
                            Gui.showPopup("QuantityWarningPopup", {
                                product: this.product,
                                quantity: quant,
                                product_image: this.get_image_url(this.product.id),
                            });
                        }
                    } else {
                        this.quantity = quant;
                        this.quantityStr = "" + this.quantity;
                        this.product["is_added"] = false;
                    }
                }
            }

            // just like in sale.order changing the quantity will recompute the unit price
            if (!keep_price && !this.price_manually_set) {
                this.set_unit_price(this.product.get_price(this.order.pricelist, this.get_quantity(), this.get_price_extra()));
                this.order.fix_tax_included_price(this);
            }

            var primary_uom = this.get_unit();
            if (this.pos.config.sh_enable_seconadry && this.pos.config.select_uom_type != 'secondary') {
                var secondary_uom = primary_uom;
                if (this.order.orderlines.models.includes(this)) {
                    this.is_secondary = true
                    secondary_uom = this.get_secondary_unit();
                }
            } 
            if (this.pos.config.sh_enable_seconadry && this.pos.config.select_uom_type == 'secondary') {
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
           
            if (this.pos.config.sh_update_quantity_cart_change && !self.pos.is_refund_button_click) {
                if (this && this.pos.db && this.pos.db.quant_by_product_id && this.product && this.product.id && this.pos.db.quant_by_product_id[this.product.id]) {
                    var actual_quantity = 0.0;
                    actual_quantity = this.pos.db.quant_by_product_id[this.product.id][this.pos.config.sh_pos_location[0]] - this.quantity
                    if(self.pack_lot_lines && self.pack_lot_lines.length > 0 && this.quantity == 1 && !old_qty){
                        actual_quantity = actual_quantity - 1;
                    }
                    var list = { product_id: [this.product.id, this.product.display_name], location_id: this.pos.config.sh_pos_location, quantity: actual_quantity };
                    $.get(
                        "/update_quanttiy",
                        {
                            passed_list: list,
                        },
                        function (result) {}
                    );
                }
            }
            
            
            this.trigger('change', this);
        },
    });
    
});
