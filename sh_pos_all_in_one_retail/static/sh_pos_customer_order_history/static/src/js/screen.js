odoo.define("sh_pos_customer_order_history.screen", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    const ClientLine = require("point_of_sale.ClientLine");
    const rpc = require("web.rpc");
    const PaymentScreen = require("point_of_sale.PaymentScreen");
    var order_list_screen = require("sh_pos_order_list.screen");
    var field_utils = require("web.field_utils");

    const SHPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            async validateOrder(isForceValidate) {
                var self = this;
                super.validateOrder(isForceValidate);

                var order = self.env.pos.get_order();
                self.formatted_validation_date = field_utils.format.datetime(moment(self.env.pos.get_order().validation_date), {}, { timezone: false });
                var lines = [];
                var sh_line_id = [];
                if (order && order.export_as_JSON().lines && order.export_as_JSON().lines.length > 0) {
                    _.each(order.export_as_JSON().lines, function (each_orderline) {
                        if (each_orderline[2] && each_orderline[2].sh_line_id) {
                            self.env.pos.db.order_line_by_uid[each_orderline[2].sh_line_id] = each_orderline[2];
                            sh_line_id.push(each_orderline[2].sh_line_id);
                        }

                        lines.push(each_orderline);
                    });
                }
                if (order && order.sh_uid && self.env.pos.db && self.env.pos.db.order_by_uid && !self.env.pos.db.order_by_uid[order.sh_uid]) {
                    if (lines && lines.length > 0) {
                        order["lines"] = lines;
                    }
                    if (sh_line_id && sh_line_id.length > 0) {
                        order["sh_line_id"] = sh_line_id;
                    }
                    if (self.formatted_validation_date) {
                        order["date_order"] = self.formatted_validation_date;
                    }
                    if (order.export_as_JSON() && order.export_as_JSON().amount_total) {
                        order["amount_total"] = order.export_as_JSON().amount_total;
                    }
                    if (order.export_as_JSON()["amount_paid"] >= parseInt(order.export_as_JSON()["amount_total"])) {
                        order["state"] = "paid";
                    } else {
                        order["state"] = "draft";
                    }
                    if (order.export_as_JSON() && order.export_as_JSON().partner_id) {
                        order["partner_id"] = order.export_as_JSON().partner_id;
                    }
                    order["pos_reference"] = order.name;
                    order["total_items"] = order.export_as_JSON().total_item;
                    order["total_qty"] = order.export_as_JSON().total_qty;
                    self.env.pos.db.all_order.push(order);
                    self.env.pos.db.order_by_uid[order.sh_uid] = order;
                }
            }
        };
    Registries.Component.extend(PaymentScreen, SHPaymentScreen);

    const Pos_order_list_screen = (order_list_screen) =>
        class extends order_list_screen {
            get posorderdetailhistory() {
                var self = this;

                if (this.state.query && this.state.query.trim() !== "") {
                    var templates = this.get_order_by_name_history(this.state.query.trim());
                    return templates;
                } else {
                    if (self.env.pos.get_order().is_client_order_filter) {
                        return self.env.pos.db.display_all_order;
                    } else {
                        return self.env.pos.db.all_order;
                    }
                }
            }
            get_order_by_name_history(name) {
                var self = this;
                if (self.env.pos.get_order().is_client_order_filter) {
                    return _.filter(self.env.pos.db.display_all_order, function (template) {
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
                } else {
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
            }
            back() {
                super.back();
                var self = this;
                var order = self.env.pos.get_order();
                order["is_client_order_filter"] = false;
            }
        };
    Registries.Component.extend(order_list_screen, Pos_order_list_screen);

    const PosClientLine = (ClientLine) =>
        class extends ClientLine {
            constructor() {
                super(...arguments);
            }
            click_order_history_icon(event) {

                var self = this;
                var client_order = [];
                var client_id = event.currentTarget.closest("tr").attributes[1].value;
                rpc.query({
                    model: "pos.order",
                    method: "search_read",
                    domain: [
                        ["user_id", "=", self.env.pos.user.id],
                        ["partner_id", "=", parseInt(client_id)],
                    ],
                })
                    .then(function (orders) {
                        if (orders) {
                            rpc.query({
                                model: "pos.order.line",
                                method: "search_read",
                            }).then(function (order_line) {
                                if (order_line) {
                                    if (order_line.length > 0) {
                                        _.each(order_line, function (each_order_line) {
                                            self.env.pos.db.order_line_by_id[each_order_line.id] = each_order_line;
                                        });
                                    }

                                    self.env.pos.get_order()["is_client_order_filter"] = true;
                                    if (orders.length > 0) {
                                        _.each(orders, function (each_order) {
                                            if (each_order.sh_uid) {
                                                self.env.pos.db.order_by_uid[each_order.sh_uid] = each_order;
                                            } else {
                                                if (each_order.id) {
                                                    self.env.pos.db.order_by_id[each_order.id] = each_order;
                                                }
                                            }
                                        });
                                    }
                                    self.env.pos["customer_order_length"] = orders.length;
                                    self.env.pos.db.display_all_order = orders;
                                    
                                    self.env.pos.db.all_display_order_temp = orders;

                                    const { confirmed, payload } = self.showTempScreen("OrderListScreen");
                                    if (confirmed) {
                                    }
                                }
                            });
                        }
                    })
                    .catch(function (reason) {
                        if (self.env.pos.db.display_all_order.length > 0 && client_id) {
                            _.each(self.env.pos.db.display_all_order, function (each_order) {
                                if (each_order.partner_id && each_order.partner_id[0] && each_order.partner_id[0] == client_id) {
                                    client_order.push(each_order);
                                } else if (each_order.partner_id && each_order.partner_id == client_id) {
                                    client_order.push(each_order);
                                }
                            });
                        }
                        if (self.env.pos.db.all_order.length > 0 && client_id) {
                            _.each(self.env.pos.db.all_order, function (each_order) {
                                if (each_order.partner_id && each_order.partner_id[0] && each_order.partner_id[0] == client_id) {
                                    client_order.push(each_order);
                                } else if (each_order.partner_id && each_order.partner_id == client_id) {
                                    client_order.push(each_order);
                                }
                            });
                        }
                        if (client_order.length > 0) {
                            var today = new Date();
                            var dd = today.getDate();
                            var mm = today.getMonth() + 1;
                            var yyyy = today.getFullYear();
                            var today_date = yyyy + "-" + mm + "-" + dd;
                            if (self.env.pos.config.sh_load_order_by == "day_wise") {
                                if (self.env.pos.config.sh_day_wise_option == "current_day") {
                                    client_order = self.env.pos.get_current_day_order(client_order);
                                } else if (self.env.pos.config.sh_day_wise_option == "last_no_day") {
                                    if (self.env.pos.config.sh_last_no_days != 0) {
                                        client_order = self.env.pos.get_last_day_order(client_order);
                                    }
                                }
                            } else if (self.env.pos.config.sh_load_order_by == "session_wise") {
                                if (self.env.pos.config.sh_session_wise_option == "current_session") {
                                    client_order = self.env.pos.get_current_session_order(client_order);
                                } else if (self.env.pos.config.sh_session_wise_option == "last_no_session") {
                                    if (self.env.pos.config.sh_last_no_session != 0) {
                                        client_order = self.env.pos.get_last_session_order(client_order);
                                    }
                                }
                            }
                        }
                        self.env.pos['customer_order_length'] = client_order.length
                        // // self.env.pos.db.display_all_order = orders;
                        self.env.pos.db.all_display_order_temp = client_order;

                        self.env.pos.get_order()["is_client_order_filter"] = true;
                        self.env.pos.db.display_all_order = client_order;
                        const { confirmed, payload } = self.showTempScreen("OrderListScreen");
                        if (confirmed) {
                        }
                        /*const { confirmed, payload } = self.showTempScreen("OrderListScreen");
                        if (confirmed) {
                        }
                        self.env.pos.get_order()["is_client_order_filter"] = true;
                        self.env.pos.db.display_all_order = client_order;*/
                    });
            }
        };
    Registries.Component.extend(ClientLine, PosClientLine);
});
