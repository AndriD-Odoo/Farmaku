odoo.define("sh_pos_order_list.screen", function (require) {
    "use strict";

    const { debounce } = owl.utils;
    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    const { useListener } = require("web.custom_hooks");
    const rpc = require("web.rpc");
    var core = require("web.core");
    var framework = require("web.framework");
    var QWeb = core.qweb;
    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const { posbus } = require("point_of_sale.utils");

    class OrderListScreen extends PosComponent {
        constructor() {
            super(...arguments);
            this.state = {
                query: null,
                selectedTemplate: this.props.template,
            };
            this.return_filter = false;
            this.updateTemplateList = debounce(this.updateTemplateList, 70);
            //            this.env.pos.db.all_order.push(this.env.pos.db.new_order[0])
            if (this.env.pos.db.all_order.length > 0) {
                var today = new Date();
                var dd = today.getDate();
                var mm = today.getMonth() + 1;
                var yyyy = today.getFullYear();
                var today_date = yyyy + "-" + mm + "-" + dd;
                if (this.env.pos.config.sh_load_order_by == "day_wise") {
                    if (this.env.pos.config.sh_day_wise_option == "current_day") {
                        this.env.pos.db.all_order = this.env.pos.get_current_day_order(this.env.pos.db.all_order);
                    } else if (this.env.pos.config.sh_day_wise_option == "last_no_day") {
                        if (this.env.pos.config.sh_last_no_days != 0) {
                            this.env.pos.db.all_order = this.env.pos.get_last_day_order(this.env.pos.db.all_order);
                        }
                    }
                } else if (this.env.pos.config.sh_load_order_by == "session_wise") {
                    if (this.env.pos.config.sh_session_wise_option == "current_session") {
                        this.env.pos.db.all_order = this.env.pos.get_current_session_order(this.env.pos.db.all_order);
                    } else if (this.env.pos.config.sh_session_wise_option == "last_no_session") {
                        if (this.env.pos.config.sh_last_no_session != 0) {
                            this.env.pos.db.all_order = this.env.pos.get_last_session_order(this.env.pos.db.all_order);
                        }
                    }
                }
            }
        }
        back() {
            this.trigger("close-temp-screen");
        }
        change_date() {
            this.state.query = $("#date1")[0].value;
            this.render();
        }
        updateOrderList(event) {

            this.state.query = event.target.value;
            const serviceorderlistcontents = this.posorderdetail;
            if (event.code === "Enter" && serviceorderlistcontents.length === 1) {
                this.state.selectedQuotation = serviceorderlistcontents[0];
            } else {
                this.render();
            }
        }
        get_order_by_name(name) {
            var self = this;
            return _.filter(self.env.pos.db.all_order, function (template) {
                if (template.name.indexOf(name) > -1) {
                    return true;
                } else if (template["pos_reference"].indexOf(name) > -1) {
                    return true;
                } else if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].toLowerCase().indexOf(name) > -1) {
                    return true;
                } else if (template["date_order"].indexOf(name) > -1) {
                    return true;
                } else {
                    return false;
                }
            });
        }
        clickLine(event) {
            var self = this;
            self.hasclass = true;
            if ($(event.currentTarget).hasClass("highlight")) {
                self.hasclass = false;
            }
            $(".sh_order_list .highlight").removeClass("highlight");
            $(event.currentTarget).closest("table").find(".show_order_detail").removeClass("show_order_detail");
            $(event.currentTarget).closest("table").find(".show_order_detail").removeClass("show_order_detail");
            $(event.currentTarget).closest("table").find(".show_order_detail").removeClass("show_order_detail");
            $(event.currentTarget).closest("table").find(".inner_data_table_row").removeClass("show_inner_data_table_row");

            var order_id = $(event.currentTarget).attr("data-order-id");
            var order_data;
            if (order_id) {
                order_data = self.env.pos.db.order_by_id[order_id];
                if (!order_data) {
                    order_data = self.env.pos.db.order_by_uid[order_id];
                }
                if (!order_data) {
                    order_id = $(event.currentTarget).attr("data-id");
                    if (order_id) {
                        order_data = self.env.pos.db.order_by_uid[order_id];
                    }
                }
            }
            if (!order_id) {
                order_id = $(event.currentTarget).attr("data-id");
                if (order_id) {
                    order_data = self.env.pos.db.order_by_uid[order_id];
                }
            }
            if (order_data && self.hasclass) {
                self.selected_pos_order = order_id;
                if (order_data.sh_line_id) {
                    _.each(order_data.sh_line_id, function (pos_order_line) {
                        $(event.currentTarget).addClass("highlight");
                        if ($(event.currentTarget).next()) {
                            $(event.currentTarget).next().addClass("show_inner_data_table_row")
                        }
                        $(event.currentTarget)
                            .closest("table")
                            .find("tr#" + order_data.pos_reference.split(" ")[1])
                            .addClass("show_order_detail");
                        $(event.currentTarget)
                            .closest("table")
                            .find("#" + pos_order_line)
                            .addClass("show_order_detail");
                    });
                } else {
                    _.each(order_data.lines, function (pos_order_line) {
                        $(event.currentTarget).addClass("highlight");
                        if ($(event.currentTarget).next()) {
                            $(event.currentTarget).next().addClass("show_inner_data_table_row")
                        }
                        $(event.currentTarget)
                            .closest("table")
                            .find("tr#" + order_data.pos_reference.split(" ")[1])
                            .addClass("show_order_detail");
                        $(event.currentTarget)
                            .closest("table")
                            .find("#" + self.env.pos.db.order_line_by_id[pos_order_line].id)
                            .addClass("show_order_detail");
                    });
                }
            }
        }
        reorder_pos_order(event) {
            var self = this;

            var order_id = $(event.currentTarget.closest("tr")).attr("data-order-id");
            var order_data;
            if (order_id) {
                order_data = self.env.pos.db.order_by_id[order_id];
                if (!order_data) {
                    order_data = self.env.pos.db.order_by_uid[order_id];
                }
                if (!order_data) {
                    order_id = $(event.currentTarget).attr("data-id");
                    if (order_id) {
                        order_data = self.env.pos.db.order_by_uid[order_id];
                    }
                }
            }
            if (!order_id) {
                order_id = $(event.currentTarget).attr("data-id");
                if (order_id) {
                    order_data = self.env.pos.db.order_by_uid[order_id];
                }
            }

            var order_line = [];

            if (self.env.pos.get_order() && self.env.pos.get_order().get_orderlines() && self.env.pos.get_order().get_orderlines().length > 0) {
                var orderlines = self.env.pos.get_order().get_orderlines();
                _.each(orderlines, function (each_orderline) {
                    if (self.env.pos.get_order().get_orderlines()[0]) {
                        self.env.pos.get_order().remove_orderline(self.env.pos.get_order().get_orderlines()[0]);
                    }
                });
            }

            var current_order = self.env.pos.get_order();

            _.each(order_data.lines, function (each_order_line) {
                var line_data = self.env.pos.db.order_line_by_id[each_order_line];
                if (!line_data) {
                    line_data = self.env.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                }
                var product = self.env.pos.db.get_product_by_id(line_data.product_id[0]);
                if (!product) {
                    product = self.env.pos.db.get_product_by_id(line_data.product_id);
                }
                if (product) {
                    current_order.add_product(product, {
                        quantity: line_data.qty,
                    });
                }
            });
            if (order_data.sh_partner_id && order_data.sh_partner_id[0] && self.env.pos.db.get_partner_by_cid(order_data['sh_partner_id'][0])) {
                self.env.pos.get_order().set_client(self.env.pos.db.get_partner_by_cid(order_data.sh_partner_id[0]));
            } else if (order_data.partner_id[0]) {
                self.env.pos.get_order().set_client(self.env.pos.db.get_partner_by_id(order_data.partner_id[0]));
            }
            current_order.assigned_config = order_data.assigned_config;
            self.trigger("close-temp-screen");
        }
        print_pos_order(event) {
            var self = this;

            var order_id = $(event.currentTarget.closest("tr")).attr("data-order-id");

            var order_data;
            if (order_id) {
                order_data = self.env.pos.db.order_by_id[order_id];
                if (!order_data) {
                    order_data = self.env.pos.db.order_by_uid[order_id];
                }
                if (!order_data) {
                    order_id = $(event.currentTarget).attr("data-id");
                    if (order_id) {
                        order_data = self.env.pos.db.order_by_uid[order_id];
                    }
                }
            }
            if (!order_id) {
                order_id = $(event.currentTarget).attr("data-id");
                if (order_id) {
                    order_data = self.env.pos.db.order_by_uid[order_id];
                }
            }

            var order_line = [];

            if (self.env.pos.get_order() && self.env.pos.get_order().get_orderlines() && self.env.pos.get_order().get_orderlines().length > 0) {
                var orderlines = self.env.pos.get_order().get_orderlines();
                _.each(orderlines, function (each_orderline) {
                    if (self.env.pos.get_order().get_orderlines()[0]) {
                        self.env.pos.get_order().remove_orderline(self.env.pos.get_order().get_orderlines()[0]);
                    }
                });
            }

            var current_order = self.env.pos.get_order();

            _.each(order_data.lines, function (each_order_line) {
                var line_data = self.env.pos.db.order_line_by_id[each_order_line];
                if (!line_data) {
                    line_data = self.env.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                }
                var product = self.env.pos.db.get_product_by_id(line_data.product_id[0]);
                if (!product) {
                    product = self.env.pos.db.get_product_by_id(line_data.product_id);
                }
                if (product) {
                    current_order.add_product(product, {
                        quantity: line_data.qty,
                    });
                }
            });
            current_order.name = order_data.pos_reference;
            current_order.assigned_config = order_data.assigned_config;
            current_order.uid = order_data.pos_reference.split(' ')[1]

            self.trigger("close-temp-screen");
            self.showScreen("ReceiptScreen");
        }
    }
    OrderListScreen.template = "OrderListScreen";
    Registries.Component.add(OrderListScreen);

    return OrderListScreen;
});
