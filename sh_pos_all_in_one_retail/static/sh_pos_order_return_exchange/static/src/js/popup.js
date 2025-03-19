odoo.define("sh_pos_order_return_signature.popup", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");

    class TemplateReturnOrderPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.lines = arguments[1].lines;
            this.order = arguments[1].order;
            this.no_return_line_id = [];
            this.return_line = [];
        }
        mounted() {
            super.mounted();
            if (this.env.pos.is_exchange) {
                $(".order_return_popup").addClass("order_exchange_popup");
            }
        }
        async confirm() {
            var self = this;
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            _.each($(".return_data_line"), function (each_data_line) {
                if (each_data_line.children[2].children[0].value != "0" && each_data_line.children[2].children[0].value != "") {
                    var order_line = self.env.pos.db.order_line_by_id[each_data_line.dataset.line_id];
                    if (!order_line) {
                        order_line = self.env.pos.db.order_line_by_uid[each_data_line.dataset.line_id];
                    }
                    order_line["old_qty"] = order_line["qty"];
                    order_line["qty"] = each_data_line.children[2].children[0].value;
//                    debugger;
                    self.return_line.push(order_line);
                } else {
                    self.no_return_line_id.push(parseInt(each_data_line.dataset.line_id));
                }
            });
            self.return_product();
            this.trigger("close-popup");
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
//                    debugger;
                    self.return_line.push(order_line);
                    self.return_product();
                } else {
                    self.no_return_line_id.push(parseInt(each_data_line.dataset.line_id));
                }
            });
        }
        return_product() {
            var self = this;
            var order_id;
            _.each($(".return_data_line"), function (each_data_line) {
                order_id = each_data_line.dataset.order_id;
            });
            order_data = self.env.pos.db.order_by_id[order_id];
            if (!order_data) {
            var order_data = self.env.pos.db.order_by_uid[order_id];
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
                current_order.is_refund_order = true;
                current_order.add_product(product, {
                    quantity: -each_line.qty,
                    price: each_line.price_unit,
                    line_id: each_line.id,
                    old_line_id: each_line.sh_line_id,
                    discount: each_line.discount,
                });
                if (order_data.sh_partner_id && order_data.sh_partner_id[0] && self.env.pos.db.get_partner_by_cid(order_data['sh_partner_id'][0])) {
                    self.env.pos.get_order().set_client(self.env.pos.db.get_partner_by_cid(order_data.sh_partner_id[0]));
                } else if (order_data.partner_id[0]) {
                    self.env.pos.get_order().set_client(self.env.pos.db.get_partner_by_id(order_data.partner_id[0]));
                }
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
            current_order.old_pos_reference = order_data.pos_reference;
            current_order.is_refund_order = false;
            this.trigger("close-popup");
            self.trigger("close-temp-screen");
            if (self.env.pos.is_return) {
                $(".pay").click();
            }
        }
        updateReturnQty(event) {
            var self = this;
            if (self.env.pos.is_return && !self.env.pos.config.sh_return_more_qty) {
                if (event.currentTarget.value) {
                    if (parseInt(event.currentTarget.value) > parseInt(event.currentTarget.closest("tr").children[1].innerText)) {
                        event.currentTarget.classList.add("more_qty");
                        event.currentTarget.value = "";
                    } else {
                        event.currentTarget.classList.remove("more_qty");
                    }
                }
            }

            if (self.env.pos.is_exchange) {
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
    }

    TemplateReturnOrderPopupWidget.template = "TemplateReturnOrderPopupWidget";
    Registries.Component.add(TemplateReturnOrderPopupWidget);

    return {
        TemplateReturnOrderPopupWidget,
    };
});
