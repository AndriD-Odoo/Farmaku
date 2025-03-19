odoo.define("sh_pos_product_bundle.ProductBundlePopup", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const { useState, useSubEnv } = owl.hooks;
    const PosComponent = require("point_of_sale.PosComponent");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");

    class ProductBundlePopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            useSubEnv({ attribute_components: [] });
        }
    }
    ProductBundlePopup.template = "ProductBundlePopup";

    Registries.Component.add(ProductBundlePopup);

    return {
        ProductBundlePopup,
    };
});
odoo.define("sh_pos_product_bundle.ProductBundleQtyPopup", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const { useState, useSubEnv } = owl.hooks;
    const PosComponent = require("point_of_sale.PosComponent");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");

    class ProductBundleQtyPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            useSubEnv({ attribute_components: [] });
        }
        captureChange(event) {
            _.each($("#bundle_product_table").find("tr.data_tr"), function (row) {
                var temp = 0;
                _.each($(row).find("input.hidden_qty"), function ($input) {
                    temp = $($input).val();
                });
                _.each($(row).find("input.qty_input"), function ($input) {
                    $($input).val(temp * event.target.value);
                });
            });
        }
    }
    ProductBundleQtyPopup.template = "ProductBundleQtyPopup";

    Registries.Component.add(ProductBundleQtyPopup);

    return {
        ProductBundleQtyPopup,
    };
});
odoo.define("sh_pos_product_bundle.screens", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var core = require("web.core");
    var rpc = require("web.rpc");
    var DB = require("point_of_sale.DB");
    var concurrency = require("web.concurrency");
    var utils = require("web.utils");
    var field_utils = require("web.field_utils");
    var Mutex = concurrency.Mutex;
    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;

    var QWeb = core.qweb;
    var _t = core._t;

    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");
    const { useBarcodeReader } = require("point_of_sale.custom_hooks");
    const { useListener } = require("web.custom_hooks");

    const BundleStockProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                useListener("click-product-bundle-icon", this.on_click_show_bundle);
            }
            async on_click_show_bundle(event) {
                const product = event.detail;
                var self = this;
                let title = product.display_name;
                let product_id = product.id;
                let product_tmpl_id = product.product_tmpl_id;
                let bundle_by_product_id = this.env.pos.db.bundle_by_product_id[product_tmpl_id];

                var table_html =
                    '<table width="100%" class="wh_qty_info"><thead><tr><th width="5%" class="head_td">No</th><th width="45%" class="head_td">Product</th><th width="5%" class="head_td">Qty</th><th width="15%" class="head_td">UOM</th><th width="15%" class="head_td">Unit Price</th><th width="15%" class="head_td">Subtotal</th></tr></thead>';
                var total_price = 0.0;
                var count = 1;
                $.each(bundle_by_product_id, function (key, value) {
                    var subtotal = value[1] * value[3];
                    total_price += subtotal;
                    table_html += '<tr><td class="data_td">' + count + '</td><td class="data_td">' + value[0][1] + "</td>";
                    table_html += '<td class="data_td">' + value[1] + '</td><td class="data_td">' + value[2][1] + "</td>";
                    table_html += '<td class="data_td">' + value[3] + '</td><td class="data_td">' + subtotal + "</td>";
                    table_html += "</tr>";
                    count += 1;
                });
                table_html += '<tr><th colspan="5" class="footer_td" style="text-align:right;">Total</th><th class="footer_td">' + total_price + "</th></tr></table>";
                let { confirmed, payload } = await this.showPopup("ProductBundlePopup", {
                    title: title,
                    body: table_html,
                });

                if (confirmed) {
                } else {
                    return;
                }
            }
            async _clickProduct(event) {
                const product = event.detail;
                if (this.env.pos.config.enable_product_bundle && product.sh_is_bundle) {
                    var self = this;
                    let title = product.display_name;
                    var product_id = product.id;
                    var product_tmpl_id = product.product_tmpl_id;
                    let bundle_by_product_id = this.env.pos.db.bundle_by_product_id[product_tmpl_id];

                    var table_html =
                        '<table width="100%" class="wh_qty" id="bundle_product_table"><thead><tr><th width="10%" class="head_td">No</th><th width="55%" class="head_td">Product</th><th width="15%" class="head_td">Qty</th><th width="20%" class="head_td">UOM</th></tr></thead>';
                    var total_price = 0.0;
                    var count = 1;
                    $.each(bundle_by_product_id, function (key, value) {
                        var subtotal = value[1] * value[3];
                        total_price += subtotal;
                        table_html += '<tr class="data_tr" data-id="' + value[0][0] + '"><td class="data_td">' + count + '</td><td class="data_td">' + value[0][1] + "</td>";
                        table_html += '<td class="data_td"><input type="hidden" class="hidden_qty" value="' + value[1] + '"/><input type="text" class="qty_input" readonly="true" value="' + value[1] + '"/></td><td class="data_td">' + value[2][1] + "</td>";
                        table_html += "</tr>";
                        count += 1;
                    });

                    let { confirmed, payload } = await this.showPopup("ProductBundleQtyPopup", {
                        title: title,
                        body: table_html,
                        price: product.lst_price.toFixed(2),
                    });

                    if (confirmed) {
                        var self = this;
                        // on confirm added all cart products in cart
                        var input_qty = $("#product_qty").val();
                        var lst_price = $("#product_price").val();

                        // get bundle products
                        _.each($("#bundle_product_table").find("tr.data_tr"), function (row) {
                            _.each($(row).find("input.qty_input"), function ($input) {
                                var product_options = {};
                                product_options["price"] = 0.0;
                                product_options["quantity"] = $($input).val();
                                var product = self.env.pos.db.product_by_id[$(row).data("id")];
                                if(product){                                	
                                	self.env.pos.get_order().add_product(product, product_options);
                                	var lines = self.env.pos.get_order().get_orderlines();
                                	for (var i = 0; i < lines.length; i++) {
                                		if (lines[i].get_product() === product) {
                                			lines[i].set_unit_price(0.0);
                                			lines[i].price_manually_set = true;
                                			return;
                                		}
                                	}
                                }
                            });
                        });

                        // Add main product
                        var main_product = self.env.pos.db.product_by_id[product_id];
                        var product_options = {};
                        product_options["quantity"] = input_qty;
                        product_options["price"] = lst_price;
                        if(main_product){                        	
                        	self.env.pos.get_order().add_product(main_product, product_options);
                        }

                        if(main_product && main_product.sh_alternative_products && main_product.sh_alternative_products.length > 0 && self.env.pos.config.sh_pos_display_alternative_products){

                            const { confirmed } = await self.showPopup('ConfirmPopup', {
                                title: this.env._t('Confirmation'),
                                body: _.str.sprintf(
                                  this.env._t('%s have Alternative Product. Do you want to see it ?'),
                                  main_product.display_name
                                ),
                            });
                            if (!confirmed) return;
                            var alternative_products = []
                            _.each(main_product.sh_alternative_products, function(each_alternative){
                                var product = self.env.pos.db.get_product_by_id(each_alternative)
                                if(product){
                                    alternative_products.push(product)
                                }
                            });
                            if(alternative_products.length > 0){
                                self.showPopup("variantPopup", { 'title': 'Alternative Product', attributes_name: [], alternative_products: alternative_products })
                            }

                        }

                        var lines = self.env.pos.get_order().get_orderlines();
                        for (var i = 0; i < lines.length; i++) {
                            if (lines[i].get_product() === product) {
                                lines[i].set_unit_price(lst_price);
                                lines[i].price_manually_set = true;
                                return;
                            }
                        }
                    } else {
                        return;
                    }
                } else {
                    super._clickProduct(...arguments);
                }
            }
            _setValue(val) {
                if (this.currentOrder.get_selected_orderline()) {
                    if (this.state.numpadMode === "quantity") {
                        var self = this;
                        if (this.currentOrder.get_selected_orderline() && this.currentOrder.get_selected_orderline().get_product()) {
                            var product = this.currentOrder.get_selected_orderline().get_product();
                            if (product.sh_is_bundle && this.env.pos.config.enable_product_bundle) {
                                var old_qty = this.currentOrder.get_selected_orderline().get_quantity();
                                var new_qty = val;
                                var update_qty = new_qty - old_qty;
                                var bundle_by_product_id = this.env.pos.db.bundle_by_product_id[product.product_tmpl_id];
                                $.each(bundle_by_product_id, function (key, value) {
                                    var bundle_product = value[0][0];
                                    // Update Qty of other bundle product
                                    var lines = self.currentOrder.get_orderlines();
                                    for (var i = 0; i < lines.length; i++) {
                                        if (lines[i].get_product().id === bundle_product) {
                                            var old_qty = lines[i].get_quantity();
                                            var new_qty = value[1] * update_qty;
                                            lines[i].set_quantity(old_qty + new_qty);
                                            return;
                                        }
                                    }
                                });
                            }
                        }

                        this.currentOrder.get_selected_orderline().set_quantity(val);
                    } else if (this.state.numpadMode === "discount") {
                        this.currentOrder.get_selected_orderline().set_discount(val);
                    } else if (this.state.numpadMode === "price") {
                        var selected_orderline = this.currentOrder.get_selected_orderline();
                        selected_orderline.price_manually_set = true;
                        selected_orderline.set_unit_price(val);
                    }
                    if (this.env.pos.config.iface_customer_facing_display) {
                        this.env.pos.send_current_order_to_customer_facing_display();
                    }
                }
            }
        };

    Registries.Component.extend(ProductScreen, BundleStockProductScreen);

    models.load_models({
        model: "sh.product.bundle",
        fields: ["id", "sh_product_id", "sh_qty", "sh_uom", "sh_price_unit", "sh_price_subtotal", "sh_bundle_id"],
        loaded: function (self, bundles) {
            self.db.add_bundles(bundles);
        },
    });
    // models.load_fields("product.template", ["sh_is_bundle"]);
    // models.load_fields("product.product", ["sh_is_bundle"]);

    DB.include({
        init: function (options) {
            this._super(options);
            this.bundles = [];
            this.bundle_by_product_id = {};
        },

        add_bundles: function (bundles) {
            if (!bundles instanceof Array) {
                bundles = [bundles];
            }
            for (var i = 0, len = bundles.length; i < len; i++) {
                var bundle = bundles[i];
                this.bundles.push(bundle);

                if (bundle.sh_bundle_id[0] in this.bundle_by_product_id) {
                    var tmp_data_list = this.bundle_by_product_id[bundle.sh_bundle_id[0]];
                    var data_list = [bundle.sh_product_id, bundle.sh_qty, bundle.sh_uom, bundle.sh_price_unit];
                    tmp_data_list.push(data_list);
                    this.bundle_by_product_id[bundle.sh_bundle_id[0]] = tmp_data_list;
                } else {
                    var data_list = [bundle.sh_product_id, bundle.sh_qty, bundle.sh_uom, bundle.sh_price_unit];
                    this.bundle_by_product_id[bundle.sh_bundle_id[0]] = [data_list];
                }
            }
        },
    });
    var _super_Orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        can_be_merged_with: function (orderline) {
            if (this.pos.config.enable_product_bundle) {
                var price = parseFloat(round_di(this.price || 0, this.pos.dp["Product Price"]).toFixed(this.pos.dp["Product Price"]));
                if (this.get_product().id !== orderline.get_product().id) {
                    //only orderline of the same product can be merged
                    return false;
                } else {
                    return true;
                }
            } else {
                return _super_Orderline.can_be_merged_with.apply(this, arguments);

            }
        },
    });

    return {
        ProductScreen,
    };
});
