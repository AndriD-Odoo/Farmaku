odoo.define("sh_pos_line_pricelist.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var DB = require("point_of_sale.DB");
    var utils = require("web.utils");
    var round_pr = utils.round_precision;
    var field_utils = require("web.field_utils");
    var round_di = utils.round_decimals;

    models.load_models({
        model: "product.pricelist",
        label: "load_pricelist",
        loaded: function (self, all_pricelist) {
            self.db.add_pricelists(all_pricelist);
        },
    });
    models.load_models({
        model: "product.pricelist.item",
        label: "load_pricelist_item",
        loaded: function (self, all_pricelist_item) {
            self.db.add_pricelist_item(all_pricelist_item);
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        add_product: function (product, options) {
            if (this._printed) {
                this.destroy();
                return this.pos.get_order().add_product(product, options);
            }
            this.assert_editable();
            options = options || {};
            var line = new models.Orderline({}, { pos: this.pos, order: this, product: product });
            line["is_added"] = true;
            this.fix_tax_included_price(line);

            if (options.quantity !== undefined) {
                line.set_quantity(options.quantity);
            }

            if (options.price !== undefined) {
                line.set_unit_price(options.price);
                this.fix_tax_included_price(line);
            }

            if (options.price_extra !== undefined) {
                line.price_extra = options.price_extra;
                line.set_unit_price(line.get_unit_price() + options.price_extra);
                this.fix_tax_included_price(line);
            }

            if (options.lst_price !== undefined) {
                line.set_lst_price(options.lst_price);
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
            if (line.is_added) {
                if (to_merge_orderline) {
                    to_merge_orderline.merge(line);
                    this.select_orderline(to_merge_orderline);
                } else {
                    this.orderlines.add(line);
                    this.select_orderline(this.get_last_orderline());
                }
            }
            if (options.draftPackLotLines) {
                this.selected_orderline.setPackLotLines(options.draftPackLotLines);
            }
            if (this.pos.config.iface_customer_facing_display) {
                this.pos.send_current_order_to_customer_facing_display();
            }
            var order = this.pos.get_order();
            if (options !== undefined) {
                if (options.line_id) {
                    order.selected_orderline.set_line_id(options.line_id);
                    order.selected_orderline.set_old_line_id(options.old_line_id);
                }
            }
        },
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            this.pricelist = false;
            _super_orderline.initialize.call(this, attr, options);
        },
        set_unit_price: function (price) {
            var self = this;
            this.min_price_pricelist;
            if (this.pos.get_order() && this.pos.get_order().get_selected_orderline) {
                var line = this.pos.get_order().get_selected_orderline();
                if (this.pos.db.get_all_pricelist() && line) {
                    _.each(this.pos.db.get_all_pricelist(), function (each_pricelist) {
                        if (each_pricelist.id == self.pos.config.sh_min_pricelist_value[0]) {
                            var price;
                            each_pricelist["items"] = [];
                            _.each(each_pricelist.item_ids, function (each_item) {
                                var item_data = self.pos.db.pricelist_item_by_id[each_item];
                                if (item_data.product_tmpl_id[0] == line.product.product_tmpl_id) {
                                    each_pricelist["items"].push(item_data);
                                    each_pricelist["product_tml_id"] = line.product.product_tmpl_id;
                                    price = line.product.get_price(each_pricelist, line.get_quantity());
                                    each_pricelist["display_price"] = price;
                                    self.min_price_pricelist = each_pricelist;
                                }
                                if (item_data.display_name == "All Products") {
                                    each_pricelist["items"].push(item_data);
                                    each_pricelist["product_tml_id"] = "All Products";
                                    price = line.product.get_price(each_pricelist, line.get_quantity());
                                    each_pricelist["display_price"] = price;
                                    self.min_price_pricelist = each_pricelist;
                                }
                            });
                        }
                    });
                }
                if (self.min_price_pricelist && self.min_price_pricelist.display_price) {
                    if (self.min_price_pricelist.product_tml_id && self.min_price_pricelist.product_tml_id == "All Products" && price < self.min_price_pricelist.display_price && self.is_added) {
                        alert("PRICE IS BELOW MINIMUM.");
                        self.is_added = false;
                    } else if (self.min_price_pricelist.product_tml_id && self.min_price_pricelist.product_tml_id == line.product.product_tmpl_id && price < self.min_price_pricelist.display_price && self.is_added) {
                        alert("PRICE IS BELOW MINIMUM.");
                        self.is_added = false;
                    } else {
                        this.order.assert_editable();
                        var parsed_price = !isNaN(price) ?
                            price :
                            isNaN(parseFloat(price)) ? 0 : field_utils.parse.float('' + price)
                        this.price = round_di(parseFloat(parsed_price) || 0, this.pos.dp["Product Price"]);
                        this.trigger("change", this);
                    }
                } else {
                    this.order.assert_editable();
                    var parsed_price = !isNaN(price) ?
                        price :
                        isNaN(parseFloat(price)) ? 0 : field_utils.parse.float('' + price)
                    this.price = round_di(parseFloat(parsed_price) || 0, this.pos.dp["Product Price"]);
                    this.trigger("change", this);
                }
            }
        },
        set_pricelist: function (pricelist) {
            this.pricelist = pricelist;
        },
        get_pricelist: function () {
            return this.pricelist || false;
        },
        export_for_printing: function () {
            var self = this;
            var lines = _super_orderline.export_for_printing.call(this);
            var new_attr = {
                pricelist: this.get_pricelist() || false,
            };
            $.extend(lines, new_attr);
            return lines;
        },
        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.call(this);
            json.pricelist = this.pricelist;
            return json;
        },
    });

    DB.include({
        init: function (options) {
            this._super(options);
            this.all_pricelists = [];
            this.all_pricelists_item = [];
            this.pricelist_by_id = {};
            this.pricelist_item_by_id = {};
        },
        add_pricelists: function (all_pricelist) {
            var self = this;
            this.all_pricelists = all_pricelist;
            _.each(this.all_pricelists, function (each_pricelist) {
                self.pricelist_by_id[each_pricelist.id] = each_pricelist;
            });
        },
        add_pricelist_item: function (all_pricelist_item) {
            var self = this;
            this.all_pricelists_item = all_pricelist_item;
            _.each(this.all_pricelists_item, function (each_pricelist_item) {
                self.pricelist_item_by_id[each_pricelist_item.id] = each_pricelist_item;
            });
        },
        get_all_pricelist: function () {
            return this.all_pricelists;
        },
    });
});
