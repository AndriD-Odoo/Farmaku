odoo.define("sh_pos_order_return_exchange_barcode.popup", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");

    class OrderReturnBarcodePopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            var self = this;
            this.lines = arguments[1].lines;

            this.order = arguments[1].order;
            this.return_line = [];
            this.no_return_line_id = [];
        }
        updateReturnQty(event) {
            var self = this;
            if ((self.env.pos.is_return && !self.env.pos.config.sh_return_more_qty) || self.env.pos.is_exchange) {
                if (event.currentTarget.value) {
                    if (parseInt(event.currentTarget.value) > parseInt(event.currentTarget.closest("tr").children[1].innerText)) {
                        event.currentTarget.classList.add("more_qty");
                        event.currentTarget.value = "";
                    } else {
                        event.currentTarget.classList.remove("more_qty");
                    }
                }
            }
        }
        click_complete_return() {
            var self = this;
            _.each($(".return_data_line"), function (each_data_line) {
                if (each_data_line.children[2].children[0].value != "0") {
                    var order_line = self.env.pos.db.order_line_by_id[each_data_line.dataset.line_id];
                    if (!order_line) {
                        order_line = self.env.pos.db.order_line_by_uid[each_data_line.dataset.line_id];
                    }
                    order_line["qty"] = each_data_line.children[1].innerText;
                    self.return_line.push(order_line);
                    self.return_product();
                } else {
                    self.no_return_line_id.push(parseInt(each_data_line.dataset.line_id));
                }
            });
        }
        mounted() {
            var self = this;
            if (self.env.pos.config.sh_allow_exchange) {
                $(".sh_same_product_checkbox").addClass("show_checkbox");
                $(".sh_return_exchange_radio").addClass("sh_exchange_order");
                self.env.pos.is_return = false;
                self.env.pos.is_exchange = true;
            }
            if (self.env.pos.config.sh_allow_return) {
                $(".sh_return_exchange_radio").removeClass("sh_exchange_order");
                $(".sh_same_product_checkbox").removeClass("show_checkbox");
                self.env.pos.is_return = true;
                self.env.pos.is_exchange = false;
            }

            $("#exchange_radio").click(function () {
                $(".sh_same_product_checkbox").addClass("show_checkbox");
                $(".sh_return_exchange_radio").addClass("sh_exchange_order");
                self.env.pos.is_return = false;
                self.env.pos.is_exchange = true;
                $(".title").text("Exchange Products");
                $(".complete_return").text("Complete Exchange");
                $(".confirm").text("Exchange");
                $(".return_exchange_popup_header").text("Exchange Qty.");
            });
            $("#return_radio").click(function () {
                $(".sh_return_exchange_radio").removeClass("sh_exchange_order");
                $(".sh_same_product_checkbox").removeClass("show_checkbox");
                self.env.pos.is_return = true;
                self.env.pos.is_exchange = false;
                $(".title").text("Return Products");
                $(".complete_return").text("Complete Return");
                $(".confirm").text("Return");
                $(".return_exchange_popup_header").text("Return Qty.");
            });
            super.mounted();
        }
        async confirm() {
            var self = this;
            if (document.getElementById("return_radio") && document.getElementById("return_radio").checked) {
                self.env.pos.is_return = true;
                self.env.pos.is_exchange = false;
            }
            if (document.getElementById("exchange_radio") && document.getElementById("exchange_radio").checked) {
                self.env.pos.is_return = false;
                self.env.pos.is_exchange = true;
            }
            _.each($(".return_data_line"), function (each_data_line) {
                if (each_data_line.children[2].children[0].value != "0" && each_data_line.children[2].children[0].value != "") {
                    var order_line = self.env.pos.db.order_line_by_id[each_data_line.dataset.line_id];
                    if (!order_line) {
                        order_line = self.env.pos.db.order_line_by_uid[each_data_line.dataset.line_id];
                    }
                    order_line["old_qty"] = order_line["qty"];
                    order_line["qty"] = each_data_line.children[2].children[0].value;
                    self.return_line.push(order_line);
                } else {
                    self.no_return_line_id.push(parseInt(each_data_line.dataset.line_id));
                }
            });
            self.return_product();
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            this.trigger("close-popup");
        }
        return_product() {
            var self = this;
            var order_id;
            _.each($(".return_data_line"), function (each_data_line) {
                order_id = each_data_line.dataset.order_id;
            });
            var order_data = self.env.pos.db.order_by_uid[order_id];
            if (!order_data) {
                order_data = self.env.pos.db.order_by_id[order_id];
            }
            var current_order = self.env.pos.get_order();

            if (self.env.pos.get_order() && self.env.pos.get_order().get_orderlines() && self.env.pos.get_order().get_orderlines().length > 0) {
                var orderlines = self.env.pos.get_order().get_orderlines();
                _.each(orderlines, function (each_orderline) {
                    if (self.env.pos.get_order().get_orderlines()[0]) {
                        self.env.pos.get_order().remove_orderline(self.env.pos.get_order().get_orderlines()[0]);
                    }
                });
            }

            var current_order = self.env.pos.get_order();
            _.each(self.return_line, function (each_line) {
                if (self.env.pos.is_return) {
                    current_order["return_order"] = true;
                }
                if (self.env.pos.is_exchange) {
                    current_order["exchange_order"] = true;
                }

                var product = self.env.pos.db.get_product_by_id(each_line.product_id[0]);
                if (!product) {
                    product = self.env.pos.db.get_product_by_id(each_line.product_id);
                }
                current_order.add_product(product, {
                    quantity: -each_line.qty,
                    price: each_line.price_unit,
                    line_id: each_line.id,
                    old_line_id: each_line.sh_line_id,
                    discount: each_line.discount,
                });
                if (self.env.pos.is_exchange && $("#exchange_checkbox")[0].checked) {
                    current_order.add_product(product, {
                        quantity: each_line.qty,
                        price: each_line.price_unit,
                        merge: false,
                        discount: each_line.discount,
                    });
                }
                if (each_line.old_qty) {
                    each_line.qty = each_line.old_qty;
                }
            });
            current_order.old_sh_uid = order_data.sh_uid;
            if (order_data.pos_reference) {
                current_order.old_pos_reference = order_data.pos_reference;
            } else {
                current_order.old_pos_reference = order_data.name;
            }
            this.trigger("close-popup");
            self.trigger("close-temp-screen");
            if (self.env.pos.is_return) {
                $(".pay").click();
            }
        }
    }

    OrderReturnBarcodePopupWidget.template = "OrderReturnBarcodePopupWidget";
    Registries.Component.add(OrderReturnBarcodePopupWidget);
});
