odoo.define("sh_pos_line_pricelist.popup", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    const { useListener } = require("web.custom_hooks");

    class PriceListPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            useListener("pricelist_row", this.onClickPricelistRow);
            var self = this;
            this.available_pricelist = [];
            this.pricelist_for_code = [];
            this.min_price_pricelist;
            var line = self.env.pos.get_order().get_selected_orderline();
            _.each(self.env.pos.db.get_all_pricelist(), function (each_pricelist) {
                if (each_pricelist.id == self.env.pos.config.sh_min_pricelist_value[0]) {
                    var price;
                    each_pricelist["items"] = [];
                    _.each(each_pricelist.item_ids, function (each_item) {
                        var item_data = self.env.pos.db.pricelist_item_by_id[each_item];

                        if (item_data.product_tmpl_id[0] == line.product.product_tmpl_id) {
                            each_pricelist["items"].push(item_data);
                            each_pricelist["product_tml_id"] = line.product.product_tmpl_id;
                        }
                        if (item_data.display_name == "All Products") {
                            each_pricelist["items"].push(item_data);
                            each_pricelist["product_tml_id"] = "All Products";
                        }
                    });

                    price = line.product.get_price(each_pricelist, line.get_quantity());
                    each_pricelist["display_price"] = price;
                    self.min_price_pricelist = each_pricelist;
                }
                if (each_pricelist.id == self.env.pos.config.sh_pricelist_for_code[0]) {
                    var price;
                    each_pricelist["items"] = [];
                    _.each(each_pricelist.item_ids, function (each_item) {
                        var item_data = self.env.pos.db.pricelist_item_by_id[each_item];
                        each_pricelist["items"].push(item_data);
                    });

                    price = line.product.get_price(each_pricelist, line.get_quantity());
                    var sNumber = price.toString();
                    var code = "";
                    _.each(sNumber, function (each_number) {
                        if (each_number == "1") {
                            code += "L";
                        }
                        if (each_number == "2") {
                            code += "U";
                        }
                        if (each_number == "3") {
                            code += "C";
                        }
                        if (each_number == "4") {
                            code += "K";
                        }
                        if (each_number == "5") {
                            code += "Y";
                        }
                        if (each_number == "6") {
                            code += "H";
                        }
                        if (each_number == "7") {
                            code += "O";
                        }
                        if (each_number == "8") {
                            code += "R";
                        }
                        if (each_number == "9") {
                            code += "S";
                        }
                        if (each_number == "0") {
                            code += "E";
                        }
                        if (each_number == ".") {
                            code += ".";
                        }
                    });
                    each_pricelist["display_price"] = code;
                    self.pricelist_for_code.push(each_pricelist);
                } else {
                    if (self.env.pos.config.available_pricelist_ids.includes(each_pricelist.id)) {
                        var price;
                        each_pricelist["items"] = [];
                        _.each(each_pricelist.item_ids, function (each_item) {
                            var item_data = self.env.pos.db.pricelist_item_by_id[each_item];
                            each_pricelist["items"].push(item_data);
                        });

                        price = line.product.get_price(each_pricelist, line.get_quantity());

                        each_pricelist["display_price"] = price;
                        self.available_pricelist.push(each_pricelist);
                    }
                }
            });
        }
        async confirm() {
            var self = this;
            self.trigger("close-popup");
        }
        async onClickPricelistRow(event) {
            var self = this;
            var line = self.env.pos.get_order().get_selected_orderline();
            $(".pricelist_row.highlight").removeClass("highlight");
            if ($(this).hasClass("highlight")) {
                $(this).removeClass("highlight");
            } else {
                $(".highlight").removeClass("highlight");
                if (!$(this).hasClass("only_read")) {
                    $(this).addClass("highlight");
                    var price = $(event.currentTarget).closest("tr").find(".price_td")[0].innerText.split(" ")[1];
                    if (self.env.pos.config.sh_min_pricelist_value) {
                        if (self.min_price_pricelist.product_tml_id && self.min_price_pricelist.product_tml_id == "All Products" && price < self.min_price_pricelist.display_price && line.is_added) {
                            alert("PRICE IS BELOW MINIMUM.");
                        } else if (self.min_price_pricelist.product_tml_id && self.min_price_pricelist.product_tml_id == line.product.product_tmpl_id && price < self.min_price_pricelist.display_price && line.is_added) {
                            alert("PRICE IS BELOW MINIMUM.");
                        } else {
                            var pricelist_data = self.env.pos.db.pricelist_by_id[$(event.currentTarget).data("id")];
                            pricelist_data["items"] = [];
                            _.each(pricelist_data.item_ids, function (each_item) {
                                var item_data = self.env.pos.db.pricelist_item_by_id[each_item];
                                pricelist_data["items"].push(item_data);
                            });
                            line.set_pricelist(pricelist_data);
                            line.set_unit_price(price);
                            self.trigger("close-popup");
                        }
                    } else {
                        var pricelist_data = self.env.pos.db.pricelist_by_id[$(event.currentTarget).data("id")];
                        pricelist_data["items"] = [];
                        _.each(pricelist_data.item_ids, function (each_item) {
                            var item_data = self.env.pos.db.pricelist_item_by_id[each_item];
                            pricelist_data["items"].push(item_data);
                        });
                        line.set_pricelist(pricelist_data);
                        line.set_unit_price(price);
                        self.trigger("close-popup");
                    }
                }
            }
        }
    }

    PriceListPopupWidget.template = "PriceListPopupWidget";
    Registries.Component.add(PriceListPopupWidget);

    return {
        PriceListPopupWidget,
    };
});
